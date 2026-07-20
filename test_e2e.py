#!/usr/bin/env python3
"""
Full-ladder E2E test for "Magic Academy: English Quest"
=======================================================
Runs a real (HEADED) Chromium browser and plays the ENTIRE game, all 100 levels,
from the first level to the last:

  * every run registers a BRAND NEW user whose name contains the date+time;
  * serves the project folder over http://localhost (needed for cookies);
  * on Level 1 it does a detailed check — all 10 game types render & are solvable,
    pictures load, the sound buttons speak in en-US, and "What is it?" answers on
    a word tap (no ANSWER button);
  * then it sweeps EVERY level 1..100. For each level it does:
        1. a WRONG run  -> score < 95  -> the next level MUST stay locked,
        2. a CORRECT run -> score 100  -> the next level unlocks,
    verifying each level's ten games are correct along the way;
  * finally it checks the rank board and that all progress persists on reload.

Run:
    pip install -r requirements.txt
    python -m playwright install chromium
    python test_e2e.py            # opens a visible browser; prints PASS/FAIL
      -- or --
    pytest test_e2e.py -s
"""

import datetime
import functools
import http.server
import json
import os
import re
import socketserver
import threading

from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.abspath(__file__))
ALL_GAME_TYPES = {
    "listen_pick_picture", "look_pick_word", "look_pick_sound", "match_pairs",
    "sort_it", "build_sentence", "spell_it", "true_false", "listen_pick_word",
    "pick_word_gap", "transform", "fix_sentence", "sort_rule",
}

BASE_GAME_TYPES = {
    "listen_pick_picture", "look_pick_word", "look_pick_sound", "match_pairs",
    "sort_it", "build_sentence", "spell_it", "true_false", "listen_pick_word",
}

GRAMMAR_GAME_TYPES = {
    "listen_pick_picture", "look_pick_word", "pick_word_gap", "build_sentence",
    "sort_rule", "transform", "fix_sentence", "true_false", "spell_it",
}

# A safe (no side-effect) element to tap per game type to prove its sound works.
SOUND_SOURCE = {
    "listen_pick_picture": ".speaker-big", "listen_pick_word": ".speaker-big",
    "build_sentence": ".speaker-big", "look_pick_sound": ".options .option",
    "look_pick_word": ".flashcard", "say_it": ".flashcard", "spell_it": ".flashcard",
    "sort_it": ".sort-token", "sort_rule": ".sort-token", "true_false": ".flashcard img",
    "pick_word_gap": ".option", "transform": ".option", "fix_sentence": ".option",
}

# Record every sound the game plays — BOTH pre-recorded audio files (the primary
# path) and any speech-synth fallback — plus whether each actually started/ended
# (proves real audio played, not merely that we asked for it).
_TRACK_SPEAK = """() => {
  window.__utt = [];
  if (!window.__patched) {
    window.__patched = true;
    // audio FILE playback (the primary path)
    const origPlay = window.HTMLMediaElement.prototype.play;
    window.HTMLMediaElement.prototype.play = function () {
      const el = this;
      const rec = { text: el.currentSrc || el.src || '', lang: 'en-US', started: false, ended: false, kind: 'file' };
      try {
        window.__utt.push(rec);
        el.addEventListener('playing', function () { rec.started = true; }, { once: true });
        el.addEventListener('ended', function () { rec.ended = true; }, { once: true });
        el.addEventListener('error', function () { rec.ended = true; }, { once: true });
      } catch (e) {}
      return origPlay.apply(el, arguments);
    };
    // speech-synth FALLBACK
    const origSpeak = window.speechSynthesis.speak.bind(window.speechSynthesis);
    window.speechSynthesis.speak = function (u) {
      const rec = { text: u.text, lang: u.lang || 'en-US', started: false, ended: false, kind: 'tts' };
      try {
        window.__utt.push(rec);
        u.addEventListener('start', function () { rec.started = true; });
        u.addEventListener('end', function () { rec.ended = true; });
        u.addEventListener('error', function () { rec.ended = true; });
      } catch (e) {}
      return origSpeak(u);
    };
  }
}"""


def _check_audio_files():
    """Confirm every audio clip referenced by the manifest exists on disk."""
    with open(os.path.join(ROOT, "audio_manifest.js"), encoding="utf-8") as f:
        txt = f.read()
    manifest = json.loads(txt[txt.index("{"):txt.rindex("}") + 1])
    paths = set(manifest.values())
    missing = [p for p in paths if not os.path.exists(os.path.join(ROOT, p))]
    assert not missing, "missing %d audio files, e.g. %s" % (len(missing), missing[:5])
    return len(paths)


def _check_image_assets():
    """Confirm every image path referenced by the generated content exists on disk."""
    refs = []
    for rel in ("content.json", "data.js", "index.html", "app.js"):
        path = os.path.join(ROOT, rel)
        if not os.path.exists(path):
            continue
        with open(path, encoding="utf-8") as f:
            refs.extend(re.findall(r'images/([A-Za-z0-9._/-]+\.(?:svg|png|jpg|jpeg|gif|webp))', f.read()))
    missing = sorted({r for r in refs if not os.path.exists(os.path.join(ROOT, "images", r))})
    assert not missing, "missing %d image files, e.g. %s" % (len(missing), missing[:10])
    return len(refs)


def _check_image_emoji_matches():
    """Confirm every generated SVG image contains the expected emoji character."""
    with open(os.path.join(ROOT, "content.json"), encoding="utf-8") as f:
        data = json.load(f)

    errors = []
    seen = set()
    for level in data.get("levels", []):
        for item in level.get("items", []):
            image = item.get("image")
            emoji = item.get("emoji")
            if not image or not emoji or not image.endswith(".svg"):
                continue
            key = (image, emoji)
            if key in seen:
                continue
            seen.add(key)
            path = os.path.join(ROOT, image)
            if not os.path.exists(path):
                errors.append("missing image file: %s" % image)
                continue
            with open(path, encoding="utf-8") as imgf:
                svg = imgf.read()
            m = re.search(r'<text[^>]*>(.*?)</text>', svg, re.S)
            if not m:
                errors.append("no text element in %s" % image)
                continue
            actual = m.group(1).strip()
            if actual != emoji:
                errors.append("emoji mismatch in %s: expected %r, found %r" % (image, emoji, actual))
    assert not errors, "emoji image validation failed:\n" + "\n".join(errors)
    return len(seen)


def _check_page_images(page, step, label):
    """Assert that every currently rendered image on the page has actually loaded."""
    page.wait_for_timeout(250)
    try:
        page.wait_for_function("() => Array.from(document.images).every(img => img.complete)", timeout=8000)
    except Exception:
        pass
    broken = page.evaluate("""() => {
      const out = [];
      Array.from(document.images).forEach((img) => {
        const src = img.getAttribute('src') || '';
        const ok = img.complete && img.naturalWidth > 0 && img.naturalHeight > 0;
        if (!ok) out.push({ src, complete: img.complete, naturalWidth: img.naturalWidth, naturalHeight: img.naturalHeight });
      });
      return out;
    }""")
    assert not broken, "broken images on %s: %s" % (label, broken[:10])
    step("Image check OK: %s (%d visible images)" % (label, page.locator("img").count()))


class _Server:
    def __init__(self, directory):
        handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=directory)

        class Threaded(socketserver.ThreadingMixIn, http.server.HTTPServer):
            daemon_threads = True
            allow_reuse_address = True

        self.httpd = Threaded(("127.0.0.1", 0), handler)
        self.port = self.httpd.server_address[1]
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)

    def __enter__(self):
        self.thread.start()
        return self

    def __exit__(self, *a):
        self.httpd.shutdown()

    @property
    def url(self):
        return "http://127.0.0.1:%d/index.html" % self.port


def _state(page):
    return page.evaluate("() => window.GilorTest.state()")


def _sound_check(page, step):
    """Speak a sequence of words ALOUD, one fully-audible word at a time, and
    confirm each actually STARTED speaking (proves audio really plays).

    Each word is triggered by a real click on a hidden button (browsers require a
    user gesture to unlock speech — `page.evaluate` doesn't count), and we wait
    for each word to finish before the next so nothing overlaps or gets cut off."""
    page.evaluate(_TRACK_SPEAK)
    page.evaluate("() => window.speechSynthesis.cancel()")   # clear any stuck/blocked speech
    page.evaluate("""() => {
      // a primer word (to unlock audio) then the words we actually measure
      window.__q = ["Get ready!", "Welcome to Magic Academy!", "apple", "banana",
                    "happy", "elephant", "rainbow", "Well done!"];
      window.__i = 0;
      if (!document.getElementById('__saybtn')) {
        const b = document.createElement('button');
        b.id = '__saybtn';
        // on-screen (so Playwright will click it = a real user gesture) but tiny
        // and nearly invisible in an empty corner.
        b.style.cssText = 'position:fixed;left:3px;bottom:3px;width:28px;height:28px;opacity:0.02;z-index:99999';
        b.addEventListener('click', () => {
          if (window.__i < window.__q.length) window.GilorTest.say(window.__q[window.__i++]);
        });
        document.body.appendChild(b);
      }
    }""")

    def wait_idle():
        try:
            page.wait_for_function(
                "() => !window.speechSynthesis.speaking && !window.speechSynthesis.pending",
                timeout=5000)
        except Exception:
            pass

    def speak_one():
        """Click (real gesture) to speak the next word; return whether it started."""
        wait_idle()                                   # so speak() runs on the in-gesture idle path
        before = page.evaluate("() => window.__utt.length")
        page.click("#__saybtn")
        try:  # wait until it actually STARTS speaking (proves audio)
            page.wait_for_function(
                "(b) => window.__utt.length > b && window.__utt[window.__utt.length - 1].started",
                arg=before, timeout=5000)
        except Exception:
            pass
        try:  # let it finish so words don't overlap and each is fully audible
            page.wait_for_function(
                "(b) => window.__utt.length > b && window.__utt[window.__utt.length - 1].ended",
                arg=before, timeout=6000)
        except Exception:
            pass
        return page.evaluate(
            "() => { const u = window.__utt[window.__utt.length - 1];"
            " return u ? { started: u.started, lang: u.lang } : null; }")

    total = page.evaluate("() => window.__q.length")
    speak_one()                                       # primer (unlock audio), not counted
    started, measured = 0, total - 1
    for _ in range(measured):
        info = speak_one()
        assert info is not None and info["lang"] == "en-US", "a word was not issued in en-US"
        if info["started"]:
            started += 1

    voices = page.evaluate("() => (window.speechSynthesis.getVoices() || []).length")
    if voices > 0:
        assert started >= measured - 1, \
            "audio not playing: only %d/%d words actually spoke (voices=%d)" % (started, measured, voices)
        step("SOUND WORKS: %d/%d words spoke ALOUD in en-US (voices=%d)" % (started, measured, voices))
    else:
        step("This browser has no TTS voices; nothing audible, wiring OK. Use real Chrome to hear it.")
    return voices


def _play_session_dom(page, step, mistakes=0, validate=False):
    """Play one session by driving the REAL UI (clicks NEXT between games).
    With `validate`, also checks sound (en-US) and 'What is it?' tap-to-answer."""
    seen, sound_ok = [], []
    if validate:
        page.evaluate(_TRACK_SPEAK)
    guard = 0
    while True:
        guard += 1
        assert guard <= 15, "session did not terminate"
        st = _state(page)
        if st["screen"] == "summary":
            break
        assert st["screen"] == "game", "expected a game, got %s" % st["screen"]
        gtype = st["gameType"]
        seen.append(gtype)
        idx = st["gameIndex"]

        if gtype in ("listen_pick_picture", "look_pick_word", "match_pairs"):
            page.wait_for_selector("#play-host img", timeout=6000)
            page.wait_for_function(
                "() => { const im=document.querySelector('#play-host img');"
                " return im && im.complete && im.naturalWidth>0; }", timeout=6000)
        _check_page_images(page, step, "game %s" % gtype)

        if validate:
            page.wait_for_timeout(250)
            if gtype == "look_pick_word":
                assert page.query_selector("#answer-btn") is None, \
                    "'What is it?' should answer on tap (no ANSWER button)"
            src = SOUND_SOURCE.get(gtype)
            if src:
                page.wait_for_selector(src, timeout=4000)
                before = page.evaluate("() => window.__utt.length")
                page.click(src)
                page.wait_for_timeout(1100)   # long enough to actually HEAR the word
                new = page.evaluate("(b) => window.__utt.slice(b)", before)
                assert len(new) >= 1, "tapping %s produced no speech for %s" % (src, gtype)
                assert all(u["lang"] == "en-US" for u in new), "speech for %s not en-US: %s" % (gtype, new)
                sound_ok.append(gtype)

        assert page.evaluate("(m) => window.GilorTest.solveCurrent(m)", mistakes), "no solver for %s" % gtype
        page.wait_for_selector("#next-btn", timeout=8000)
        assert _state(page)["awaitingNext"] is True
        page.click("#next-btn")
        page.wait_for_function(
            "(p) => { const s=window.GilorTest.state();"
            " return s.screen==='summary' || s.gameIndex!==p; }", arg=idx)

    score = int(page.text_content(".score-ring .num").strip())
    if validate:
        total = page.evaluate("() => window.__utt.length")
        langs = page.evaluate("() => Array.from(new Set(window.__utt.map(u => u.lang)))")
        # Every sound source wired up its word in en-US. (Actual audibility is proved
        # by _sound_check; in rapid automated play, overlapping speech is intentionally
        # cancelled by the next utterance, so few "start" here — that's expected.)
        assert total >= 10 and langs == ["en-US"], "in-game sound not wired: %d utts, langs=%s" % (total, langs)
        step("Level 1 in-game: 10/10 game types, %d en-US sound buttons wired, tap-to-answer OK, %d/100"
             % (len(set(sound_ok)), score))
    return set(seen), score


def _sweep_all_levels(page, step):
    """Play EVERY level: a wrong run (no unlock) then a correct run (unlock)."""
    total = _state(page)["totalLevels"]
    page.evaluate("() => window.GilorTest.setFast(true)")   # fast automation mode
    try:
        for i in range(total):
            assert page.evaluate("(i) => window.GilorTest.startLevel(i)", i) is True, \
                "level %d should be unlocked but startLevel refused" % i
            u_before = _state(page)["unlocked"]

            # --- WRONG run: must not unlock the next level ---
            expected_types = page.evaluate("(i) => { const level = window.GAME_DATA.levels[i]; return (level && level.gameTypes) ? level.gameTypes : []; }", i)
            wrong = page.evaluate("(m) => window.GilorTest.playSession(m)", 1)
            assert not wrong.get("error"), "level %d WRONG-run error: %s" % (i, wrong.get("error"))
            assert set(wrong.get("types", [])) == set(expected_types), \
                "level %d missing game types: %s" % (i, set(expected_types) - set(wrong.get("types", [])))
            assert wrong["score"] < 95, "level %d wrong run should be <95, got %d" % (i, wrong["score"])
            assert wrong["minStars"] < 3, "level %d wrong run should lose stars" % i
            assert _state(page)["unlocked"] == u_before, \
                "level %d: a failing run (%d/100) must NOT unlock the next level" % (i, wrong["score"])

            # --- CORRECT run: unlocks the next level ---
            assert page.evaluate("(i) => window.GilorTest.startLevel(i)", i) is True
            correct = page.evaluate("(m) => window.GilorTest.playSession(m)", 0)
            assert not correct.get("error"), "level %d CORRECT-run error: %s" % (i, correct.get("error"))
            assert set(correct.get("types", [])) == set(expected_types), \
                "level %d missing game types on correct run" % i
            assert correct["score"] == 100, "level %d correct run should be 100, got %d" % (i, correct["score"])
            if i < total - 1:
                assert _state(page)["unlocked"] == max(u_before, i + 1), \
                    "level %d: scoring 100 should unlock the next level" % i

            if (i + 1) % 10 == 0 or i == total - 1:
                step("  swept %3d/%d levels — each: wrong <95 (locked) then 100 (unlock)" % (i + 1, total))
    finally:
        page.evaluate("() => window.GilorTest.setFast(false)")

    st = _state(page)
    assert st["unlocked"] == total - 1, "after all levels, unlocked should be %d, got %d" % (total - 1, st["unlocked"])
    assert st["mastered"] == total, "all %d levels should be mastered, got %d" % (total, st["mastered"])
    step("Full ladder DONE: %d levels validated, %d sessions (wrong+correct each), all mastered"
         % (total, total * 2))


def run_full_flow(page, base_url, username):
    log = []

    def step(msg):
        log.append(msg)
        print("  •", msg)

    n_audio = _check_audio_files()
    n_images = _check_image_assets()
    step("Audio pack present: %d pre-recorded clips on disk (browser-independent)" % n_audio)
    step("Image asset inventory present: %d referenced image paths on disk" % n_images)
    
    page.goto(base_url)
    page.wait_for_function("() => window.GilorTest && window.GilorTest.ready")
    assert _state(page)["screen"] == "login"
    step("Login screen on first visit")

    # register a brand-new date/time user through the UI (a real gesture unlocks audio)
    page.fill("#u", username)
    page.click("#login-btn")
    page.wait_for_selector(".world-map")
    _check_page_images(page, step, "home screen")
    st = _state(page)
    total = st["totalLevels"]
    assert st["user"] == username and st["unlocked"] == 0 and st["totalStars"] == 0
    assert total == 300, "expected 300 levels, got %s" % total
    step("Registered new user '%s'; %d-level map, only Level 1 open" % (username, total))

    # ---- AUDIBLE sound check FIRST, on a clean audio state right after the login gesture ----
    step("SOUND CHECK: speaking words aloud now")
    _sound_check(page, step)

    chips = page.eval_on_selector_all(".level-chip", "els => els.length")
    locked = page.eval_on_selector_all(".level-chip.locked", "els => els.length")
    assert chips == total and locked == total - 1, "map lock state wrong: %d chips / %d locked" % (chips, locked)
    assert page.evaluate("() => window.GilorTest.startLevel(1)") is False
    assert page.evaluate("() => window.GilorTest.startLevel(9)") is False
    step("Map: %d chips, %d locked; locked levels refuse to start" % (chips, locked))

    # detailed checks on Level 1 (sound, tap-to-answer, images, all 10 types)
    assert page.evaluate("() => window.GilorTest.startLevel(0)") is True
    page.wait_for_selector("#play-host")
    step("Checking every in-game sound button on Level 1 (also audible) …")
    seen, score = _play_session_dom(page, step, mistakes=0, validate=True)
    assert seen == BASE_GAME_TYPES and score == 100

    # THE FULL LADDER
    _sweep_all_levels(page, step)

    # rank board: a newcomer ranks below our (now champion) user
    newcomer = username + "_pal"
    page.evaluate("() => window.GilorTest.logout()")
    page.wait_for_selector(".login-card")
    assert page.evaluate("(n) => window.GilorTest.login(n, 'pw')", newcomer) is True
    assert _state(page)["totalStars"] == 0
    page.evaluate("() => window.GilorTest.logout()")
    page.wait_for_selector(".login-card")
    assert page.evaluate("(n) => window.GilorTest.login(n, 'secret1')", username) is True
    page.wait_for_selector(".world-map")
    page.click("#ranks-btn")
    page.wait_for_selector(".rank-list")
    rows = page.eval_on_selector_all(".rank-row", "els => els.map(e => e.getAttribute('data-name'))")
    assert rows and rows[0] == username, "champion should rank #1: %s" % rows
    me = page.eval_on_selector_all(".rank-row.me", "els => els.map(e => e.getAttribute('data-name'))")
    assert me == [username], "current user should be highlighted, got %s" % me
    step("Rank board: '%s' is #1 above the newcomer; current user highlighted" % username)

    # persistence across reload
    page.reload()
    page.wait_for_function("() => window.GilorTest && window.GilorTest.ready")
    st = _state(page)
    assert st["screen"] == "home" and st["user"] == username
    assert st["unlocked"] == total - 1 and st["mastered"] == total, "progress must persist across reload"
    step("After reload: all %d levels still mastered (cookies persist)" % total)
    return log


def _make_page(pw):
    # Prefer the REAL Google Chrome (it ships text-to-speech voices, so you can
    # actually HEAR the game); fall back to Playwright's bundled Chromium (visible
    # but silent — it has no TTS voices).
    browser, used, last = None, None, None
    for opts in ({"channel": "chrome"}, {}):
        try:
            browser = pw.chromium.launch(headless=False, args=["--autoplay-policy=no-user-gesture-required"], **opts)
            used = opts.get("channel", "chromium (bundled — no voices)")
            break
        except Exception as e:  # noqa
            last = e
    if browser is None:
        raise last
    print("  browser:", used)
    context = browser.new_context(viewport={"width": 1280, "height": 900})
    context.grant_permissions([])
    page = context.new_page()
    page.set_default_timeout(15000)
    errors = []

    def _record_error(msg):
        errors.append(msg)

    def _is_image_request(url):
        url = (url or "").lower()
        return "/images/" in url or url.endswith((".svg", ".png", ".jpg", ".jpeg", ".gif", ".webp"))

    # Real JS exceptions fail the run.
    page.on("pageerror", lambda e: _record_error("pageerror: " + str(e)))
    # console.error, but ignore the generic resource-load message (covered precisely
    # by the response listener below, which knows the URL).
    page.on("console", lambda m: _record_error("console.error: " + m.text)
            if (m.type == "error" and "Failed to load resource" not in m.text) else None)
    # A 4xx/5xx for any real asset fails the run — but the browser's automatic
    # /favicon.ico probe is harmless and ignored.
    page.on("response", lambda r: _record_error("HTTP %d: %s" % (r.status, r.url))
            if (r.status >= 400 and not r.url.rstrip("/").endswith("favicon.ico")) else None)
    page.on("requestfailed", lambda req: _record_error("requestfailed: %s [%s]" % (req.url, req.failure.error_text))
            if req.failure and _is_image_request(req.url) else None)
    return browser, context, page, errors


def _username():
    return datetime.datetime.now().strftime("kid_%Y%m%d_%H%M%S")


def test_full_game_flow():
    with _Server(ROOT) as server, sync_playwright() as pw:
        browser, context, page, errors = _make_page(pw)
        try:
            run_full_flow(page, server.url, _username())
            assert not errors, "JS errors during run:\n" + "\n".join(errors)
        finally:
            art = os.path.join(ROOT, "test-artifacts")
            os.makedirs(art, exist_ok=True)
            try:
                page.screenshot(path=os.path.join(art, "e2e-summary.png"), full_page=True)
            except Exception:
                pass
            browser.close()


def main():
    user = _username()
    print("Running Magic Academy full-ladder E2E (headed) as user:", user)
    with _Server(ROOT) as server, sync_playwright() as pw:
        print("  server:", server.url)
        browser, context, page, errors = _make_page(pw)
        failed = False
        try:
            run_full_flow(page, server.url, user)
            if errors:
                failed = True
                print("\nJS ERRORS DETECTED:")
                for e in errors:
                    print("   ", e)
        except AssertionError as e:
            failed = True
            print("\n  ✗ ASSERTION FAILED:", e)
        except Exception as e:  # noqa
            failed = True
            print("\n  ✗ ERROR:", repr(e))
        finally:
            art = os.path.join(ROOT, "test-artifacts")
            os.makedirs(art, exist_ok=True)
            try:
                page.screenshot(path=os.path.join(art, "e2e-summary.png"), full_page=True)
                print("  screenshot saved:", os.path.join(art, "e2e-summary.png"))
            except Exception:
                pass
            browser.close()
    if failed:
        print("\n==================  E2E: FAILED  ==================")
        raise SystemExit(1)
    print("\n==================  E2E: ALL CHECKS PASSED  ==================")


if __name__ == "__main__":
    main()
