#!/usr/bin/env python3
"""
build_audio.py  —  Magic Academy: English Quest
================================================
Generates REAL audio files (American accent) for every word, sentence, praise
line, feedback line and instruction, so the game NEVER depends on the browser's
text-to-speech engine.

    python3 build_audio.py            # generate missing files
    python3 build_audio.py --force    # regenerate everything

How: on macOS, `say` (voice "Samantha", en-US) -> AIFF -> `afconvert` -> small .m4a
(AAC). On Windows, the script uses the built-in SpeechSynthesizer to write .wav
files. Files land in ./audio and a text->file map is written to audio_manifest.js
(loaded by index.html; consumed by app.js).
"""

import concurrent.futures as cf
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
AUDIO_DIR = os.path.join(HERE, "audio")
VOICE = "Samantha"     # clear en-US (American) voice
RATE = "165"           # words per minute — a touch slow for a young learner

# Fixed UI phrases the app speaks (must match the strings in app.js exactly).
FIXED_PHRASES = [
    "Hello! Let's play!",
    "Pick a level to play!",
    "Here is the rank board!",
    "Choose an answer!",
    "Let's try the next one!",
    "This level is locked. Score 95 to unlock it!",
    "Keep practising!",
    "Yes",
    "No",
    "Get ready!",
    "Welcome to Magic Academy!",
]


def norm(t):
    return re.sub(r"\s+", " ", t).strip()


def slugify(text):
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return (s or "clip")[:50]


def collect_texts():
    with open(os.path.join(HERE, "content.json"), encoding="utf-8") as f:
        data = json.load(f)
    texts = []
    seen = set()

    def add(t):
        t = norm(t)
        if t and t not in seen:
            seen.add(t)
            texts.append(t)

    for lv in data["levels"]:
        add(lv["name"])                 # topic / group name (Sort It group boxes speak this)
        for it in lv["items"]:
            add(it["word"])
        for s in lv["sentences"]:
            add(s)
        g = lv.get("grammar") or {}
        if g:
            add(g.get("target", ""))
            for e in g.get("gap", []):
                add(e.get("text", "").replace("___", e.get("options", [""])[e.get("correct", 0)]))
                for o in e.get("options", []): add(o)
            for e in g.get("transform", []):
                add(e.get("prompt", "")); add(e.get("base", ""))
                for o in e.get("options", []): add(o)
            for e in g.get("fix", []):
                add(e.get("right", "")); add(e.get("wrong", ""))
            s = g.get("sort")
            if s:
                add(s.get("binA", "")); add(s.get("binB", ""))
                for t in s.get("tokens", []): add(t.get("t", ""))
    for p in data.get("praise", []):
        add(p)
    for p in data.get("tryAgain", []):
        add(p)
    for gt in data.get("gameTypes", []):
        add(gt["instruction"])
    for p in FIXED_PHRASES:
        add(p)
    return texts


def audio_ext():
    if sys.platform == "darwin":
        return ".m4a"
    return ".wav"


def build_manifest(texts):
    """text -> audio/<unique-slug>.<ext>"""
    ext = audio_ext()
    manifest, used = {}, set()
    for t in texts:
        base = slugify(t)
        slug, n = base, 2
        while slug in used:
            slug = "%s-%d" % (base, n)
            n += 1
        used.add(slug)
        manifest[t] = "audio/%s%s" % (slug, ext)
    return manifest


def generate_one(text, rel_path, force):
    out = os.path.join(HERE, rel_path)
    if os.path.exists(out) and not force:
        return ("skip", text)
    if sys.platform == "darwin":
        aiff = out[:-4] + ".aiff"
        try:
            subprocess.run(["say", "-v", VOICE, "-r", RATE, "-o", aiff, text],
                           check=True, capture_output=True)
            subprocess.run(["afconvert", "-f", "m4af", "-d", "aac", aiff, out],
                           check=True, capture_output=True)
            return ("ok", text)
        except subprocess.CalledProcessError as e:
            return ("fail:" + (e.stderr.decode(errors="ignore")[:80] if e.stderr else "?"), text)
        finally:
            if os.path.exists(aiff):
                os.remove(aiff)
    elif os.name == "nt":
        try:
            safe_text = text.replace("'", "''")
            script = (
                "$ErrorActionPreference='Stop'; "
                "Add-Type -AssemblyName System.Speech; "
                "$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
                "try { $synth.SetOutputToWaveFile('{out}'); $synth.Speak('{text}') } "
                "finally { $synth.Dispose() }"
            ).replace('{out}', out.replace("'", "''")).replace('{text}', safe_text)
            subprocess.run(["powershell", "-NoProfile", "-Command", script],
                           check=True, capture_output=True, text=True)
            return ("ok", text)
        except subprocess.CalledProcessError as e:
            msg = (e.stderr or e.stdout or "")
            return ("fail:" + msg[:120].replace("\n", " "), text)
    else:
        return ("fail:unsupported-platform", text)


def main():
    if sys.platform != "darwin" and os.name != "nt":
        print("This generator needs macOS (`say`/`afconvert`) or Windows speech support.")
        sys.exit(1)
    force = "--force" in sys.argv
    os.makedirs(AUDIO_DIR, exist_ok=True)

    texts = collect_texts()
    manifest = build_manifest(texts)

    print("Generating %d audio clips (voice=%s)…" % (len(texts), VOICE))
    ok = skip = fail = 0
    with cf.ThreadPoolExecutor(max_workers=8) as ex:
        futs = [ex.submit(generate_one, t, manifest[t], force) for t in texts]
        for i, fut in enumerate(cf.as_completed(futs), 1):
            status, _ = fut.result()
            if status == "ok":
                ok += 1
            elif status == "skip":
                skip += 1
            else:
                fail += 1
                print("  !", status)
            if i % 100 == 0:
                print("  … %d/%d" % (i, len(texts)))

    # normalized-text -> path (app.js normalizes lookups the same way)
    man_norm = {norm(k): v for k, v in manifest.items()}
    with open(os.path.join(HERE, "audio_manifest.js"), "w", encoding="utf-8") as f:
        f.write("/* AUTO-GENERATED by build_audio.py — text -> audio file. */\n")
        f.write("window.AUDIO_MANIFEST = ")
        json.dump(man_norm, f, ensure_ascii=False, indent=1)
        f.write(";\n")

    total_bytes = sum(os.path.getsize(os.path.join(HERE, p))
                      for p in manifest.values() if os.path.exists(os.path.join(HERE, p)))
    print("Done: %d generated, %d skipped, %d failed. %d clips, %.1f MB total."
          % (ok, skip, fail, len(manifest), total_bytes / 1e6))


if __name__ == "__main__":
    main()
