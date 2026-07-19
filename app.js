/* ==========================================================================
   Magic Academy: English Quest  —  app.js
   A self-contained English learning game for young beginners.

     1.  DOM + random helpers
     2.  Cookies + profile persistence (stars, unlocked level, per-level scores)
     3.  Audio module (Web Speech API, American / en-US accent)
     4.  Feedback FX (verbal praise, banner, confetti)
     5.  Picture / prompt builders (pictures speak their word when tapped)
     6.  Auth (login / register)
     7.  Screens: login, home world-map, rank board, game host, summary
     8.  Session engine: 10-game session, scoring, star + unlock persistence
     9.  The 10 game types
     10. window.GilorTest hooks (for the Playwright E2E)
   ========================================================================== */
(function () {
  "use strict";

  var DATA = window.GAME_DATA;
  var UNLOCK_SCORE = (DATA.meta && DATA.meta.unlockScore) || 95;
  var TOTAL_LEVELS = DATA.levels.length;
  // Automation-only "fast" mode: skips cosmetic delays/animations and audio so
  // the full-ladder E2E can play thousands of games quickly. Off for real play.
  var FAST = false;
  // Grading: a level starts at 100 and loses 1 point for EVERY wrong tap/answer.
  // So >5 mistakes in a level => grade < 95 => the next level stays locked.
  // Skipping a game (🚩) costs a bigger penalty so it can't be a free pass.
  var SKIP_PENALTY = 10;

  /* ============================ 1. Helpers ============================ */
  function $(sel, root) { return (root || document).querySelector(sel); }
  function el(tag, props, children) {
    var n = document.createElement(tag);
    props = props || {};
    for (var k in props) {
      if (!Object.prototype.hasOwnProperty.call(props, k)) continue;
      var v = props[k];
      if (v == null) continue;
      if (k === "class") n.className = v;
      else if (k === "html") n.innerHTML = v;
      else if (k === "text") n.textContent = v;
      else if (k === "style" && typeof v === "object") Object.assign(n.style, v);
      else if (k.slice(0, 2) === "on" && typeof v === "function") n.addEventListener(k.slice(2).toLowerCase(), v);
      else n.setAttribute(k, v);
    }
    var kids = Array.prototype.slice.call(arguments, 2);
    kids.forEach(function add(kid) {
      if (kid == null || kid === false) return;
      if (Array.isArray(kid)) return kid.forEach(add);
      n.appendChild(typeof kid === "object" ? kid : document.createTextNode(String(kid)));
    });
    return n;
  }
  function randInt(n) { return Math.floor(Math.random() * n); }
  function pick(arr) { return arr[randInt(arr.length)]; }
  function shuffle(arr) {
    var a = arr.slice();
    for (var i = a.length - 1; i > 0; i--) { var j = randInt(i + 1); var t = a[i]; a[i] = a[j]; a[j] = t; }
    return a;
  }
  function sample(arr, n) { return shuffle(arr).slice(0, n); }
  function distractors(pool, excludeWords, n) {
    return shuffle(pool).filter(function (it) { return excludeWords.indexOf(it.word) < 0; }).slice(0, n);
  }

  /* ============================ 2. Cookies ============================ */
  function canUseLocalStorage() {
    try { return typeof window.localStorage !== "undefined" && window.localStorage !== null; } catch (e) { return false; }
  }
  function setCookie(name, value, days) {
    if (canUseLocalStorage()) {
      try { window.localStorage.setItem(name, value); return; } catch (e) { }
    }
    var exp = "";
    if (days) { var d = new Date(); d.setTime(d.getTime() + days * 864e5); exp = "; expires=" + d.toUTCString(); }
    document.cookie = name + "=" + encodeURIComponent(value) + exp + "; path=/; SameSite=Lax";
  }
  function getCookie(name) {
    if (canUseLocalStorage()) {
      try { var val = window.localStorage.getItem(name); if (val != null) return val; } catch (e) { }
    }
    var m = document.cookie.match("(?:^|; )" + name.replace(/([.$?*|{}()\[\]\\\/\+^])/g, "\\$1") + "=([^;]*)");
    return m ? decodeURIComponent(m[1]) : null;
  }
  function delCookie(name) {
    if (canUseLocalStorage()) {
      try { window.localStorage.removeItem(name); return; } catch (e) { }
    }
    document.cookie = name + "=; Max-Age=0; path=/";
  }

  var PROFILES_KEY = "mae_profiles";
  var CURRENT_KEY = "mae_current";

  function getProfiles() { try { return JSON.parse(getCookie(PROFILES_KEY) || "{}"); } catch (e) { return {}; } }
  function saveProfiles(p) { setCookie(PROFILES_KEY, JSON.stringify(p), 365); }
  function obfuscate(s) { try { return btoa(unescape(encodeURIComponent(s))); } catch (e) { return s; } }

  // Ensure a profile has every field (migration-safe).
  function normalize(p) {
    p = p || {};
    if (p.stars == null) p.stars = 0;
    if (p.sessions == null) p.sessions = 0;
    if (p.best == null) p.best = 0;
    if (p.unlocked == null) p.unlocked = 0;      // highest unlocked level index
    if (!p.levelScores) p.levelScores = {};        // levelId -> best score
    return p;
  }
  function currentUsername() { return getCookie(CURRENT_KEY); }
  function currentProfile() {
    var u = currentUsername(); if (!u) return null;
    var p = getProfiles(); return p[u] ? normalize(p[u]) : null;
  }
  function mutateProfile(fn) {
    var u = currentUsername(); if (!u) return;
    var p = getProfiles(); if (!p[u]) return;
    p[u] = normalize(p[u]); fn(p[u]); saveProfiles(p);
  }
  function masteredCount(prof) {
    var n = 0, ls = (prof && prof.levelScores) || {};
    for (var k in ls) if (ls[k] >= UNLOCK_SCORE) n++;
    return n;
  }

  /* ============================ 3. Audio ============================== */
  function normText(t) { return String(t == null ? "" : t).replace(/\s+/g, " ").trim(); }

  var Audio = {
    supported: typeof window.speechSynthesis !== "undefined",
    manifest: window.AUDIO_MANIFEST || {},
    current: null,              // currently-playing HTMLAudioElement
    voice: null, _ready: false, _token: 0, _ka: null,

    // Play a pre-recorded file if we have one for this text; otherwise fall back
    // to the browser's speech engine. Pre-recorded files (in ./audio) mean the
    // game does NOT depend on the browser having text-to-speech voices.
    speak: function (text, opts) {
      opts = opts || {}; var done = opts.onend || function () { };
      if (FAST) { setTimeout(done, 0); return; }
      if (opts.mute) { setTimeout(done, 10); return; }
      var file = this.manifest[normText(text)];
      if (file) { this._playFile(file, done); return; }
      this._speakSynth(text, opts, done);
    },
    _playFile: function (path, done) {
      var self = this, called = false;
      function fin() { if (!called) { called = true; done(); } }
      try {
        if (this.current) { try { this.current.pause(); } catch (e) { } this.current.onended = null; this.current = null; }
        var a = new window.Audio(path);
        this.current = a;
        a.onended = fin; a.onerror = fin;
        var p = a.play();
        if (p && p.catch) p.catch(function () { fin(); });  // autoplay blocked -> resolve
        setTimeout(fin, 8000);
      } catch (e) { setTimeout(fin, 10); }
    },

    warm: function () {
      if (!this.supported) return;
      this._pickVoice();
      var self = this;
      if (window.speechSynthesis.onvoiceschanged === null)
        window.speechSynthesis.onvoiceschanged = function () { self._pickVoice(); };
      try { window.speechSynthesis.resume(); } catch (e) { }
      // Chrome quietly pauses speech synthesis after a while; nudge it awake.
      if (!this._ka) this._ka = setInterval(function () {
        try { if (window.speechSynthesis.paused) window.speechSynthesis.resume(); } catch (e) { }
      }, 8000);
    },
    _pickVoice: function () {
      if (!this.supported) return;
      var voices;
      try { voices = window.speechSynthesis.getVoices() || []; } catch (e) { voices = []; }
      if (!voices.length) return;
      var prefer = ["Samantha", "Alex", "Aaron", "Nicky", "Google US English", "Microsoft Aria", "Microsoft Zira"];
      var us = voices.filter(function (v) { return /en[-_]US/i.test(v.lang); });
      var byName = null;
      for (var i = 0; i < prefer.length && !byName; i++) {
        byName = us.filter(function (v) { return v.name.indexOf(prefer[i]) >= 0; })[0] ||
          voices.filter(function (v) { return v.name.indexOf(prefer[i]) >= 0; })[0];
      }
      this.voice = byName || us[0] || voices.filter(function (v) { return /^en/i.test(v.lang); })[0] || voices[0];
      this._ready = true;
    },
    _speakSynth: function (text, opts, done) {
      opts = opts || {}; done = done || function () { };
      if (!this.supported || !text) { setTimeout(done, 10); return; }
      var self = this, synth = window.speechSynthesis;
      try {
        if (!this._ready) this._pickVoice();
        var u = new SpeechSynthesisUtterance(String(text));
        u.lang = "en-US";
        if (this.voice) u.voice = this.voice;
        u.rate = opts.rate || 0.92; u.pitch = opts.pitch || 1.05; u.volume = 1;
        var called = false;
        function finish() { if (!called) { called = true; done(); } }
        u.onend = finish; u.onerror = finish;
        var token = ++this._token;
        function doSpeak() {
          if (token !== self._token) { finish(); return; }   // superseded by a newer speak()
          if (!self.voice) { self._pickVoice(); if (self.voice) u.voice = self.voice; }
          try { synth.resume(); } catch (e) { }
          try { synth.speak(u); } catch (e) { finish(); }
        }
        var busy = false;
        try { busy = synth.speaking || synth.pending; } catch (e) { }
        if (busy) {
          // Interrupting speech: Chrome/Safari DROP an utterance if speak() runs in
          // the same tick as cancel(), so cancel now and speak after a short gap.
          try { synth.cancel(); } catch (e) { }
          setTimeout(doSpeak, 60);
        } else {
          // Idle: speak immediately so the call stays inside the user gesture
          // (required to unlock audio) and no cancel/speak race can drop it.
          doSpeak();
        }
        setTimeout(finish, 6000);
      } catch (e) { setTimeout(done, 10); }
    }
  };

  /* ========================= 4. Feedback FX =========================== */
  var FX = {
    layer: null,
    ensure: function () { if (!this.layer) this.layer = $("#fx-layer"); return this.layer; },
    banner: function (text, good) {
      if (FAST) return;
      var layer = this.ensure(); layer.innerHTML = "";
      var b = el("div", { class: "feedback-banner" + (good ? "" : " bad") },
        el("div", { class: "mascot" }, good ? pick(DATA.mascots) : "🤔"),
        el("div", { class: "bubble" }, text));
      layer.appendChild(b); void b.offsetWidth; b.classList.add("show");
      if (good) this.confetti();
      clearTimeout(this._t);
      this._t = setTimeout(function () { b.classList.remove("show"); }, 1600);
    },
    confetti: function () {
      if (FAST) return;
      var layer = this.ensure();
      var colors = ["#ffd33a", "#4ad15b", "#58b6ff", "#ff5a6a", "#b984ff", "#ff9f43"];
      var cx = window.innerWidth / 2, cy = window.innerHeight / 2;
      for (var i = 0; i < 26; i++) (function (i) {
        var c = el("div", { class: "confetti" });
        c.style.background = colors[i % colors.length];
        c.style.left = cx + "px"; c.style.top = cy + "px";
        layer.appendChild(c);
        var ang = Math.random() * Math.PI * 2, dist = 120 + Math.random() * 220;
        var dx = Math.cos(ang) * dist, dy = Math.sin(ang) * dist - 80;
        c.style.transition = "transform .9s cubic-bezier(.15,.6,.3,1), opacity .9s ease";
        requestAnimationFrame(function () {
          c.style.transform = "translate(" + dx + "px," + dy + "px) rotate(" + (Math.random() * 720) + "deg)";
          c.style.opacity = "0";
        });
        setTimeout(function () { c.remove(); }, 950);
      })(i);
    }
  };

  /* ==================== 5. Picture / prompt builders ================== */
  // A picture ALWAYS speaks its word when tapped (learning aid, everywhere).
  function picNode(item, opts) {
    opts = opts || {};
    var speak = opts.speak !== false;
    var img = document.createElement("img");
    img.src = item.image; img.alt = item.word; img.draggable = false;
    if (speak) {
      img.style.cursor = "pointer";
      img.title = "Tap to hear";
      img.addEventListener("click", function () { Audio.speak(item.word); });
    }
    img.onerror = function () {
      var span = el("div", { class: "emoji-pic" }, item.emoji);
      if (speak) {
        span.style.cursor = "pointer";
        span.addEventListener("click", function () { Audio.speak(item.word); });
      }
      if (img.parentNode) img.parentNode.replaceChild(span, img);
    };
    return img;
  }
  function speakerPrompt(text) {
    var b = el("button", { class: "speaker-big", "aria-label": "Listen" }, "🔊");
    b.addEventListener("click", function () {
      b.classList.add("playing");
      Audio.speak(text, { onend: function () { b.classList.remove("playing"); } });
    });
    return b;
  }
  function flashcard(item, o) {
    o = o || {};
    var fc = el("div", { class: "flashcard" });
    var cardSpeak = o.speak !== false;
    var pictureSpeak = o.pictureSpeak !== false;
    if (cardSpeak) {
      // Tapping ANYWHERE on the card (emoji, word, or padding) says the word.
      fc.style.cursor = "pointer";
      fc.title = "Tap to hear";
      fc.addEventListener("click", function () { Audio.speak(o.spokenText || item.word); });
      var sp = el("button", { class: "corner-speaker", "aria-label": "Listen" }, "🔊");
      sp.addEventListener("click", function (e) { e.stopPropagation(); Audio.speak(o.spokenText || item.word); });
      fc.appendChild(sp);
    }
    fc.appendChild(picNode(item, { speak: pictureSpeak }));
    if (o.label) fc.appendChild(el("div", { class: "word-label" }, o.labelText || item.word));
    return fc;
  }

  /* ============================ App / Engine ========================== */
  var App = {
    root: null, session: null,
    _solver: null, _wrongSolver: null, _mistakes: 0, awaitingNext: false,

    start: function () {
      this.root = $("#app"); Audio.warm();
      if (currentUsername() && currentProfile()) this.renderHome();
      else this.renderLogin();
      window.GilorTest.ready = true;
    },

    /* ------------------------------- Login ------------------------------ */
    renderLogin: function (msg) {
      Audio.warm(); var self = this; this.root.innerHTML = "";
      var userIn, passIn, msgBox;
      var card = el("div", { class: "login-card" },
        el("div", { class: "logo" }, "🚀"),
        el("h1", {}, "Magic Academy"),
        el("p", { class: "tag" }, "English Quest — learn & play!"),
        el("div", { class: "field" }, el("label", { for: "u" }, "Your name"),
          (userIn = el("input", { id: "u", type: "text", autocomplete: "off", placeholder: "e.g. Tzofia", maxlength: "20" }))),
        el("div", { class: "field" }, el("label", { for: "p" }, "Secret word (password)"),
          (passIn = el("input", { id: "p", type: "password", autocomplete: "off", placeholder: "your secret word" }))),
        (msgBox = el("div", { class: "login-msg" }, msg || "")),
        el("button", { class: "btn btn-answer", id: "login-btn" }, "Let's Go! ▶"),
        el("p", { class: "login-hint" }, "New here? Just type a name and secret word to begin."));
      this.root.appendChild(el("div", { class: "login-wrap" }, card));

      function submit() {
        Audio.warm();
        var u = (userIn.value || "").trim(), p = (passIn.value || "").trim();
        if (!u) { msgBox.textContent = "Please type your name."; return; }
        if (!p) { msgBox.textContent = "Please type a secret word."; return; }
        var profiles = getProfiles();
        if (profiles[u]) {
          if (profiles[u].pass !== obfuscate(p)) { msgBox.textContent = "That secret word is wrong. Try again!"; Audio.speak("Try again!"); return; }
        } else {
          profiles[u] = normalize({ pass: obfuscate(p) }); saveProfiles(profiles);
        }
        setCookie(CURRENT_KEY, u, 365);
        Audio.speak("Hello! Let's play!");
        self.renderHome();
      }
      $("#login-btn").addEventListener("click", submit);
      passIn.addEventListener("keydown", function (e) { if (e.key === "Enter") submit(); });
      userIn.addEventListener("keydown", function (e) { if (e.key === "Enter") passIn.focus(); });
    },
    logout: function () { delCookie(CURRENT_KEY); this.session = null; this.renderLogin(); },

    starBadge: function () {
      var prof = currentProfile() || { stars: 0 };
      return el("div", { class: "star-badge", id: "star-badge" },
        el("span", { class: "star" }, "⭐"),
        el("span", { class: "count", id: "star-count" }, String(prof.stars || 0)));
    },
    refreshStars: function () {
      var c = $("#star-count");
      if (c) { c.textContent = String((currentProfile() || {}).stars || 0); c.parentNode.classList.add("wiggle"); setTimeout(function () { c.parentNode.classList.remove("wiggle"); }, 300); }
    },

    /* ------------------------------- Home ------------------------------- */
    renderHome: function () {
      var self = this; this.root.innerHTML = "";
      var u = currentUsername();
      var prof = currentProfile() || normalize({});
      var unlocked = prof.unlocked || 0;
      var current = Math.min(unlocked, TOTAL_LEVELS - 1);

      var top = el("div", { class: "topbar" },
        el("button", { class: "circle-btn", title: "Log out", "aria-label": "Log out", onclick: function () { self.logout(); } }, "⎋"),
        el("div", { class: "title-mid" }, "Magic Academy"),
        this.starBadge());

      var hero = el("div", { class: "home-hero" },
        el("h1", {}, "Hi, " + u + "! 👋"),
        el("div", { class: "who" }, "Level " + (current + 1) + " of " + TOTAL_LEVELS +
          "  •  ⭐ " + (prof.stars || 0) + " stars  •  " + masteredCount(prof) + " mastered"));

      var actions = el("div", { class: "home-actions" },
        el("button", { class: "btn btn-answer", id: "continue-btn", onclick: function () { self.startSession(current); } },
          "▶ Play Level " + (current + 1)),
        el("button", { class: "btn btn-ghost", id: "ranks-btn", onclick: function () { self.renderRanks(); } }, "🏆 Ranks"));

      // world map
      var map = el("div", { class: "world-map", id: "world-map" });
      var worlds = [];
      DATA.levels.forEach(function (lv) {
        var w = worlds[lv.worldIndex];
        if (!w) { w = worlds[lv.worldIndex] = { name: lv.world, sub: lv.worldSubtitle, levels: [] }; }
        w.levels.push(lv);
      });
      worlds.forEach(function (w) {
        var grid = el("div", { class: "level-grid" });
        w.levels.forEach(function (lv) {
          var isUnlocked = lv.index <= unlocked;
          var best = prof.levelScores[lv.id] || 0;
          var mastered = best >= UNLOCK_SCORE;
          var cls = "level-chip" + (!isUnlocked ? " locked" : mastered ? " mastered" : "") + (lv.index === current ? " current" : "");
          var chip = el("button", {
            class: cls, disabled: isUnlocked ? null : "true", "data-index": lv.index, "data-id": lv.id,
            onclick: isUnlocked ? function () { self.startSession(lv.index); } : null,
            title: isUnlocked ? lv.name : "Score " + UNLOCK_SCORE + "+ on the level before to unlock"
          },
            el("div", { class: "chip-num" }, isUnlocked ? String(lv.index + 1) : "🔒"),
            el("div", { class: "chip-name" }, lv.name),
            el("div", { class: "chip-foot" }, mastered ? "✓ " + best : (best ? String(best) : (isUnlocked ? "play" : "")))
          );
          grid.appendChild(chip);
        });
        map.appendChild(el("div", { class: "world-block" },
          el("div", { class: "world-head" },
            el("span", { class: "world-name" }, w.name),
            el("span", { class: "world-sub" }, w.sub)),
          grid));
      });

      var screen = el("div", { class: "screen home" }, top, hero, actions, map);
      this.root.appendChild(screen);
      // bring the current level into view
      var cur = $(".level-chip.current");
      if (cur && cur.scrollIntoView) try { cur.scrollIntoView({ block: "center" }); } catch (e) { }
      Audio.speak("Pick a level to play!");
    },

    /* ---------------------------- Rank board ---------------------------- */
    renderRanks: function () {
      var self = this; this.root.innerHTML = "";
      var me = currentUsername();
      var profiles = getProfiles();
      var rows = Object.keys(profiles).map(function (name) {
        var p = normalize(profiles[name]);
        return { name: name, stars: p.stars || 0, best: p.best || 0, mastered: masteredCount(p) };
      });
      rows.sort(function (a, b) { return (b.stars - a.stars) || (b.best - a.best) || (b.mastered - a.mastered) || a.name.localeCompare(b.name); });

      var top = el("div", { class: "topbar" },
        el("button", { class: "circle-btn", "aria-label": "Home", onclick: function () { self.renderHome(); } }, "‹"),
        el("div", { class: "title-mid" }, "🏆 Rank Board"),
        this.starBadge());

      var list = el("div", { class: "rank-list", id: "rank-list" });
      var medals = ["🥇", "🥈", "🥉"];
      rows.forEach(function (r, i) {
        list.appendChild(el("div", { class: "rank-row" + (r.name === me ? " me" : ""), "data-name": r.name },
          el("div", { class: "rank-pos" }, i < 3 ? medals[i] : "#" + (i + 1)),
          el("div", { class: "rank-name" }, r.name, r.name === me ? el("span", { class: "badge-you" }, "YOU") : null),
          el("div", { class: "rank-stat" }, "⭐ " + r.stars),
          el("div", { class: "rank-stat" }, "🏅 " + r.mastered),
          el("div", { class: "rank-stat" }, "🎯 " + r.best)));
      });
      if (!rows.length) list.appendChild(el("div", { class: "rank-empty" }, "No players yet!"));

      var legend = el("div", { class: "rank-legend" }, "⭐ total stars   •   🏅 levels mastered   •   🎯 best score");
      var screen = el("div", { class: "screen" }, top, el("div", { class: "play rank-play" }, el("h1", { class: "rank-title" }, "Top Explorers"), list, legend));
      this.root.appendChild(screen);
      Audio.speak("Here is the rank board!");
    },

    /* --------------------------- Session setup -------------------------- */
    // ref may be a level index (number) or level id (string). Returns true if started.
    startSession: function (ref) {
      var level = (typeof ref === "number")
        ? DATA.levels[ref]
        : DATA.levels.filter(function (l) { return l.id === ref; })[0];
      if (!level) return false;
      var prof = currentProfile() || normalize({});
      if (level.index > (prof.unlocked || 0)) {
        Audio.speak("This level is locked. Score " + UNLOCK_SCORE + " to unlock it!");
        FX.banner("🔒 Locked! Score " + UNLOCK_SCORE + "+ first", false);
        return false;
      }
      var pool = level.items.slice();
      var typeIds = (level.gameTypes && level.gameTypes.length)
        ? level.gameTypes.slice()
        : DATA.gameTypes.map(function (g) { return g.id; });
      var order = shuffle(typeIds);
      this.session = { level: level, pool: pool, sentences: level.sentences, order: order, index: 0, mistakes: 0, results: [], spellWordsUsed: [] };
      this.renderGame();
      return true;
    },

    /* --------------------------- Game host ------------------------------ */
    renderGame: function () {
      var self = this, s = this.session;
      var typeId = s.order[s.index];
      var gt = DATA.gameTypes.filter(function (g) { return g.id === typeId; })[0];
      this._mistakes = 0; this._solver = null; this._wrongSolver = null; this.awaitingNext = false;
      this.root.innerHTML = "";

      var top = el("div", { class: "topbar" },
        el("button", { class: "circle-btn", "aria-label": "Home", onclick: function () { self.renderHome(); } }, "‹"),
        el("div", { class: "title-mid" }, "Level " + (s.level.index + 1) + " · " + gt.name + " · " + s.level.name),
        this.starBadge());

      var dots = el("div", { class: "progress" });
      for (var i = 0; i < s.order.length; i++)
        dots.appendChild(el("div", { class: "dot" + (i < s.index ? " done" : i === s.index ? " current" : "") }));

      var host = el("div", { class: "play", id: "play-host" });
      var bottom = el("div", { class: "bottombar", id: "bottombar" });
      this.root.appendChild(el("div", { class: "screen" }, top, dots, host, bottom));

      var answerHandler = null;
      var api = {
        pool: s.pool, sentences: s.sentences, level: s.level, allLevels: DATA.levels,
        el: el, pick: pick, shuffle: shuffle, sample: sample, distractors: distractors,
        picNode: picNode, flashcard: flashcard, speakerPrompt: speakerPrompt,
        speak: function (t, o) { Audio.speak(t, o); },
        addMistake: function () { self._mistakes++; if (self.session) self.session.mistakes++; },
        wrong: function () { FX.banner(pick(DATA.tryAgain), false); Audio.speak(pick(DATA.tryAgain)); },
        nudge: function () { Audio.speak("Choose an answer!"); },
        session: s,
        markSpellWordUsed: function (word) {
          if (!s || !word) return;
          var key = String(word).toLowerCase();
          if (s.spellWordsUsed.indexOf(key) < 0) s.spellWordsUsed.push(key);
        },
        finish: function () { self.completeGame(false); },
        registerSolver: function (fn) { self._solver = fn; },
        registerWrongSolver: function (fn) { self._wrongSolver = fn; },
        setInstruction: function (node) {
          var ins = el("div", { class: "instruction" });
          if (typeof node === "string") ins.appendChild(document.createTextNode(node));
          else ins.appendChild(node);
          host.insertBefore(ins, host.firstChild);
        },
        setAnswerHandler: function (fn) { answerHandler = fn; renderBottom(); },
        enableAnswer: function (on) { var b = $("#answer-btn"); if (b) b.disabled = !on; },
        clickAnswer: function () { if (answerHandler) answerHandler(); }
      };

      function renderBottom() {
        bottom.innerHTML = "";
        bottom.appendChild(el("button", { class: "btn btn-skip", title: "Skip", "aria-label": "Skip", onclick: function () { self.completeGame(true); } }, "🚩"));
        bottom.appendChild(el("div", { class: "spacer" }));
        bottom.appendChild(el("button", { class: "btn btn-ghost", "aria-label": "Repeat", onclick: function () { Audio.speak(gt.instruction); } }, "🔁"));
        if (answerHandler)
          bottom.appendChild(el("button", { class: "btn btn-answer", id: "answer-btn", disabled: "true", onclick: function () { if (answerHandler) answerHandler(); } }, "ANSWER"));
      }
      renderBottom();
      Audio.speak(gt.instruction);
      GAMES[typeId](host, api);
    },

    /* ------------------------- Complete a game -------------------------- */
    completeGame: function (skipped) {
      if (this.awaitingNext) return;
      var self = this, s = this.session;
      var gt = DATA.gameTypes.filter(function (g) { return g.id === s.order[s.index]; })[0];
      var m = this._mistakes;
      var stars = skipped ? 0 : (m === 0 ? 3 : m <= 2 ? 2 : 1);
      if (skipped) s.mistakes += SKIP_PENALTY;   // a skipped game hurts the grade

      s.results.push({ type: gt.id, name: gt.name, stars: stars });
      if (stars > 0) { mutateProfile(function (p) { p.stars += stars; }); this.refreshStars(); }

      this.awaitingNext = true;
      if (skipped) { FX.banner("Let's try the next one!", false); Audio.speak("Let's try the next one!"); }
      else { var msg = pick(DATA.praise); FX.banner(msg + "  " + "⭐".repeat(stars), true); Audio.speak(msg); }

      var host = $("#play-host"); if (host) host.style.pointerEvents = "none";
      var bottom = $("#bottombar");
      if (bottom) {
        bottom.innerHTML = "";
        var last = s.index >= s.order.length - 1;
        bottom.appendChild(el("div", { class: "spacer" }));
        bottom.appendChild(el("button", { class: "btn btn-next", id: "next-btn", onclick: function () { self.next(); } },
          last ? "See my score ⭐" : "NEXT ▶"));
      }
    },
    next: function () {
      if (!this.awaitingNext) return;
      this.awaitingNext = false;
      var s = this.session;
      if (s.index >= s.order.length - 1) { this.renderSummary(); return; }
      s.index++; this.renderGame();
    },

    /* ------------------------------ Summary ----------------------------- */
    renderSummary: function () {
      var self = this, s = this.session;
      var score = Math.max(0, 100 - s.mistakes);   // 100 minus every wrong tap/answer
      var lvl = s.level;
      var earned = s.results.reduce(function (a, r) { return a + r.stars; }, 0);
      var maxStars = s.results.length * 3;

      // persist best score, session count, and unlock the next level on >=95
      var unlockedNew = false, nextIndex = lvl.index + 1;
      mutateProfile(function (p) {
        p.sessions += 1;
        p.best = Math.max(p.best, score);
        p.levelScores[lvl.id] = Math.max(p.levelScores[lvl.id] || 0, score);
        if (score >= UNLOCK_SCORE && nextIndex < TOTAL_LEVELS && p.unlocked < nextIndex) {
          p.unlocked = nextIndex; unlockedNew = true;
        }
      });

      var passed = score >= UNLOCK_SCORE;
      var tier = score >= 95 ? "Superstar! 🌟" : score >= 80 ? "Great work! 🎉" : score >= 60 ? "Good job! 👍" : "Keep practising! 💪";
      var hasNext = nextIndex < TOTAL_LEVELS;

      this.root.innerHTML = "";
      var top = el("div", { class: "topbar" },
        el("button", { class: "circle-btn", "aria-label": "Home", onclick: function () { self.renderHome(); } }, "‹"),
        el("div", { class: "title-mid" }, "Level " + (lvl.index + 1) + ": " + lvl.name),
        this.starBadge());

      var breakdown = el("div", { class: "breakdown" });
      s.results.forEach(function (r) {
        breakdown.appendChild(el("div", {}, r.name));
        breakdown.appendChild(el("div", { class: "b-star" }, r.stars > 0 ? "⭐".repeat(r.stars) : "—"));
      });

      var unlockMsg;
      if (passed && hasNext && unlockedNew) unlockMsg = el("div", { class: "unlock-msg good", id: "unlock-msg" }, "🔓 You unlocked Level " + (nextIndex + 1) + "!");
      else if (passed && hasNext) unlockMsg = el("div", { class: "unlock-msg good", id: "unlock-msg" }, "✓ Level " + (nextIndex + 1) + " is open!");
      else if (passed && !hasNext) unlockMsg = el("div", { class: "unlock-msg good", id: "unlock-msg" }, "🏆 You finished every level!");
      else unlockMsg = el("div", { class: "unlock-msg", id: "unlock-msg" }, "Score " + UNLOCK_SCORE + "+ to unlock the next level. Try again!");

      var btnRow = el("div", { class: "btn-row" });
      if (passed && hasNext)
        btnRow.appendChild(el("button", { class: "btn btn-answer", id: "next-level-btn", onclick: function () { self.startSession(nextIndex); } }, "Next level ▶"));
      btnRow.appendChild(el("button", { class: "btn btn-next", id: "replay-btn", onclick: function () { self.startSession(lvl.index); } }, "Play again ↻"));
      btnRow.appendChild(el("button", { class: "btn btn-ghost", onclick: function () { self.renderHome(); } }, "🏠 Map"));

      var summary = el("div", { class: "summary" },
        el("h1", {}, tier),
        el("div", { class: "score-ring" + (passed ? " pass" : "") }, el("div", {},
          el("div", { class: "num", id: "final-score" }, String(score)), el("div", { class: "of" }, "/ 100"))),
        el("div", { class: "stars-earned" }, "⭐ " + earned + " / " + maxStars + " stars this round"),
        unlockMsg, breakdown, btnRow);

      this.root.appendChild(el("div", { class: "screen" }, top, el("div", { class: "play" }, summary)));
      Audio.speak(passed ? pick(DATA.praise) : "Keep practising!");   // random praise on success
      if (passed) FX.confetti();
    }
  };

  /* ============================ 9. Games ============================== */
  // Single-choice helper: prompt + option grid + ANSWER. Registers correct +
  // wrong solvers for the E2E. `speakWord`: speak the option's word on select.
  function singleChoice(host, api, cfg) {
    if (cfg.promptNode) host.appendChild(cfg.promptNode);
    var instant = !!cfg.instant;   // instant: tap an option to answer (no ANSWER button)
    var grid = el("div", { class: "options" + (cfg.twoUp ? " two" : "") });
    var nodes = [], selected = -1, solved = false;

    function judge(i) {
      if (solved) return;
      if (i === cfg.correct) { solved = true; nodes[i].classList.add("correct"); api.finish(); return; }
      var bad = nodes[i]; bad.classList.add("wrong");
      api.addMistake(); api.wrong(); selected = -1;
      if (!instant) api.enableAnswer(false);
      setTimeout(function () { bad.classList.remove("wrong", "selected"); }, 450);
    }

    cfg.options.forEach(function (data, i) {
      var o = el("div", { class: "option", role: "button", tabindex: "0" });
      o.appendChild(cfg.renderOption(data, i));
      o.addEventListener("click", function () {
        if (solved || o.classList.contains("correct")) return;
        if (cfg.onSelect) cfg.onSelect(data);
        nodes.forEach(function (nn) { nn.classList.remove("selected"); });
        o.classList.add("selected");
        if (instant) { judge(i); return; }
        selected = i;
        api.enableAnswer(true);
      });
      grid.appendChild(o); nodes.push(o);
    });
    host.appendChild(grid);

    if (!instant) {
      api.setAnswerHandler(function () {
        if (solved) return;
        if (selected < 0) { api.nudge(); return; }
        judge(selected);
      });
    }
    api.registerSolver(function () { nodes[cfg.correct].click(); if (!instant) api.clickAnswer(); });
    api.registerWrongSolver(function () {
      var w = (cfg.correct + 1) % nodes.length;
      nodes[w].click(); if (!instant) api.clickAnswer();
    });
  }

  var GAMES = {
    listen_pick_picture: function (host, api) {
      var target = api.pick(api.pool);
      var opts = api.shuffle([target].concat(api.distractors(api.pool, [target.word], 3)));
      api.setInstruction("👂 Listen and tap the picture");
      singleChoice(host, api, {
        promptNode: api.speakerPrompt(target.word), options: opts, correct: opts.indexOf(target), instant: true,
        renderOption: function (d) { return api.picNode(d, { speak: false }); }
      });
      api.speak(target.word);
    },

    look_pick_word: function (host, api) {
      var target = api.pick(api.pool);
      var opts = api.shuffle([target].concat(api.distractors(api.pool, [target.word], 3)));
      api.setInstruction("👀 What is it? Tap the word");
      singleChoice(host, api, {
        promptNode: api.flashcard(target, { speak: true, spokenText: target.word }),
        options: opts, correct: opts.indexOf(target), instant: true,
        onSelect: function (d) { api.speak(d.word); },
        renderOption: function (d) { return el("span", {}, d.word); }
      });
    },

    look_pick_sound: function (host, api) {
      var target = api.pick(api.pool);
      var opts = api.shuffle([target].concat(api.distractors(api.pool, [target.word], 3)));
      api.setInstruction("🔊 Tap the sounds. Which one is it?");
      singleChoice(host, api, {
        promptNode: api.flashcard(target, { speak: false, pictureSpeak: false }), options: opts, correct: opts.indexOf(target),
        onSelect: function (d) { api.speak(d.word); },
        renderOption: function () { return el("span", { class: "speaker-inner" }, "🔊"); }
      });
    },

    listen_pick_word: function (host, api) {
      var target = api.pick(api.pool);
      var opts = api.shuffle([target].concat(api.distractors(api.pool, [target.word], 3)));
      api.setInstruction("👂 Listen and tap the word");
      singleChoice(host, api, {
        promptNode: api.speakerPrompt(target.word), options: opts, correct: opts.indexOf(target), instant: true,
        renderOption: function (d) { return el("span", {}, d.word); }
      });
      api.speak(target.word);
    },

    true_false: function (host, api) {
      var item = api.pick(api.pool);
      var truth = Math.random() < 0.5;
      var spoken = truth ? item : api.distractors(api.pool, [item.word], 1)[0];
      var isMatch = spoken.word === item.word;
      api.setInstruction("🤔 Is this right?");
      var prompt = api.flashcard(item, { speak: false, pictureSpeak: true, spokenText: item.word });
      prompt.appendChild(el("div", { class: "word-label" }, spoken.word + "?"));
      singleChoice(host, api, {
        promptNode: prompt, twoUp: true, options: [{ v: "yes" }, { v: "no" }], correct: isMatch ? 0 : 1, instant: true,
        renderOption: function (d) { return el("span", { style: { fontSize: "2em" } }, d.v === "yes" ? "✅" : "❌"); }
      });
    },

    match_pairs: function (host, api) {
      var pairs = api.sample(api.pool, 4);
      api.setInstruction("🔗 Match each picture to its word");
      var wrap = el("div", { class: "match-wrap" });
      var colL = el("div", { class: "match-col" }), colR = el("div", { class: "match-col" });
      wrap.appendChild(colL); wrap.appendChild(colR); host.appendChild(wrap);

      var selected = null, matched = 0, leftNodes = {}, rightNodes = {};
      function tryPair(a, b) {
        if (a.word === b.word) {
          a.el.classList.add("matched"); b.el.classList.add("matched"); matched++; api.speak(a.word);
          if (matched === pairs.length) setTimeout(function () { api.finish(); }, FAST ? 0 : 300);
        } else {
          a.el.classList.add("wrong"); b.el.classList.add("wrong"); api.addMistake(); api.wrong();
          setTimeout(function () { a.el.classList.remove("wrong"); b.el.classList.remove("wrong"); }, 450);
        }
      }
      function handler(entry) {
        if (entry.el.classList.contains("matched")) return;
        if (!selected) { selected = entry; entry.el.classList.add("selected"); return; }
        if (selected.el === entry.el) { entry.el.classList.remove("selected"); selected = null; return; }
        if (selected.col === entry.col) { selected.el.classList.remove("selected"); selected = entry; entry.el.classList.add("selected"); return; }
        var a = selected, b = entry; selected.el.classList.remove("selected"); selected = null; tryPair(a, b);
      }
      api.shuffle(pairs).forEach(function (it) {
        var node = el("div", { class: "match-item", role: "button" }); node.appendChild(api.picNode(it, { speak: false }));
        var entry = { el: node, word: it.word, col: "L" };
        node.addEventListener("click", function () { handler(entry); });
        colL.appendChild(node); leftNodes[it.word] = entry;
      });
      api.shuffle(pairs).forEach(function (it) {
        var node = el("div", { class: "match-item", role: "button" }, el("span", { class: "speaker-inner" }, "🔊"));
        var entry = { el: node, word: it.word, col: "R" };
        node.addEventListener("click", function () { api.speak(it.word); handler(entry); });
        colR.appendChild(node); rightNodes[it.word] = entry;
      });
      api.registerSolver(function () { pairs.forEach(function (p) { leftNodes[p.word].el.click(); rightNodes[p.word].el.click(); }); });
    },

    sort_it: function (host, api) {
      if (api.level.grammar && api.level.grammar.sort) return GAMES.sort_rule(host, api);
      // category A = this level; category B = a different level's items
      var others = api.allLevels.filter(function (l) { return l.id !== api.level.id && l.items.length >= 2; });
      var B = api.pick(others);
      var A = api.level;
      var tokens = api.shuffle(
        A.items.map(function (x) { return { it: x, cat: "A" }; })
          .concat(B.items.map(function (x) { return { it: x, cat: "B" }; })));
      api.setInstruction("📦 Put each word in the right box");

      var idx = 0;
      var current = el("div", { class: "sort-current" });
      var binsRow = el("div", { class: "sort-wrap" });
      var binA = makeBin(A.name, "A"), binB = makeBin(B.name, "B");
      binsRow.appendChild(binA.node); binsRow.appendChild(binB.node);
      host.appendChild(current); host.appendChild(binsRow);

      function makeBin(title, cat) {
        var items = el("div", { class: "bin-items" });
        var speaker = el("button", { class: "bin-speaker", "aria-label": "Hear group name" }, "🔊");
        speaker.addEventListener("click", function (e) { e.stopPropagation(); api.speak(title); });
        var head = el("div", { class: "bin-title" }, speaker, el("span", {}, title));
        var node = el("div", { class: "bin", role: "button" }, head, items);
        node.addEventListener("click", function () { place(cat, node); });
        return { node: node, items: items };
      }
      function renderCurrent() {
        current.innerHTML = "";
        if (idx >= tokens.length) return;
        var t = tokens[idx];
        var tok = el("div", { class: "sort-token", role: "button", title: "Tap to hear" }, el("span", {}, t.it.word));
        tok.addEventListener("click", function (e) { if (e.target === tok || e.target.tagName === "SPAN") api.speak(t.it.word); });
        current.appendChild(tok);
        api.speak(t.it.word);
      }
      function binFor(cat) { return cat === "A" ? binA : binB; }
      function place(cat, node) {
        if (idx >= tokens.length) return;
        var t = tokens[idx];
        if (cat === t.cat) {
          var chip = el("div", { class: "sort-token" }, el("span", {}, t.it.word));
          binFor(t.cat).items.appendChild(chip); idx++;
          if (idx >= tokens.length) { current.innerHTML = ""; setTimeout(function () { api.finish(); }, FAST ? 0 : 250); }
          else renderCurrent();
        } else { node.classList.add("wrong"); api.addMistake(); api.wrong(); setTimeout(function () { node.classList.remove("wrong"); }, 450); }
      }
      renderCurrent();
      api.registerSolver(function () { var g = 0; while (idx < tokens.length && g < 60) { binFor(tokens[idx].cat).node.click(); g++; } });
      api.registerWrongSolver(function () { if (idx < tokens.length) binFor(tokens[idx].cat === "A" ? "B" : "A").node.click(); });
    },

    pick_word_gap: function (host, api) {
      var grammar = api.level.grammar || {};
      var gap = api.pick(grammar.gap || []);
      if (!gap) { api.finish(); return; }
      var promptText = gap.text.replace("___", "____");
      api.setInstruction("🧩 Tap the missing word");
      var prompt = el("div", { class: "flashcard" });
      prompt.appendChild(el("div", { class: "word-label" }, promptText));
      if (gap.emoji) prompt.appendChild(el("div", { class: "emoji-pic" }, gap.emoji));
      singleChoice(host, api, {
        promptNode: prompt,
        options: gap.options.map(function (o) { return { text: o }; }),
        correct: gap.correct || 0,
        instant: true,
        onSelect: function (d) { api.speak(d.text); },
        renderOption: function (d) { return el("span", {}, d.text); }
      });
      api.speak(gap.text.replace("___", gap.options[gap.correct || 0]));
    },

    transform: function (host, api) {
      var grammar = api.level.grammar || {};
      var item = api.pick(grammar.transform || []);
      if (!item) { api.finish(); return; }
      api.setInstruction("🔧 Make the right word");
      var prompt = el("div", { class: "flashcard" });
      prompt.appendChild(el("div", { class: "word-label" }, item.prompt));
      singleChoice(host, api, {
        promptNode: prompt,
        options: item.options.map(function (o) { return { text: o }; }),
        correct: item.correct || 0,
        instant: true,
        onSelect: function (d) { api.speak(d.text); },
        renderOption: function (d) { return el("span", {}, d.text); }
      });
      api.speak(item.base);
    },

    fix_sentence: function (host, api) {
      var grammar = api.level.grammar || {};
      var item = api.pick(grammar.fix || []);
      if (!item) { api.finish(); return; }
      api.setInstruction("🕵️ Which one is right?");
      var prompt = null;
      if (item.emoji) prompt = el("div", { class: "flashcard" });
      if (prompt) { prompt.appendChild(el("div", { class: "emoji-pic" }, item.emoji)); }
      var options = [{ text: item.right }, { text: item.wrong }];
      var shuffled = api.shuffle(options.slice());
      var correct = shuffled.findIndex(function (o) { return o.text === item.right; });
      singleChoice(host, api, {
        promptNode: prompt,
        twoUp: true,
        options: shuffled,
        correct: correct,
        instant: true,
        onSelect: function (d) { api.speak(d.text); },
        renderOption: function (d) { return el("div", { class: "word-label" }, d.text); }
      });
      api.registerSolver(function () { var node = host.querySelectorAll(".option")[correct]; if (node) node.click(); });
      api.registerWrongSolver(function () { var node = host.querySelectorAll(".option")[correct === 0 ? 1 : 0]; if (node) node.click(); });
      api.speak(item.right);
    },

    sort_rule: function (host, api) {
      if (!api.level.grammar || !api.level.grammar.sort) return GAMES.sort_it(host, api);
      var sort = api.level.grammar.sort;
      api.setInstruction("📦 Put each one in the right box");
      var tokens = api.shuffle(sort.tokens.slice());
      var idx = 0;
      var current = el("div", { class: "sort-current" });
      var binsRow = el("div", { class: "sort-wrap" });
      var binA = makeBin(sort.binA || "A", "A");
      var binB = makeBin(sort.binB || "B", "B");
      binsRow.appendChild(binA.node); binsRow.appendChild(binB.node);
      host.appendChild(current); host.appendChild(binsRow);

      function makeBin(title, cat) {
        var items = el("div", { class: "bin-items" });
        var node = el("div", { class: "bin", role: "button" }, el("div", { class: "bin-title" }, el("span", {}, title)), items);
        node.addEventListener("click", function () { place(cat, node); });
        return { node: node, items: items };
      }
      function renderCurrent() {
        current.innerHTML = "";
        if (idx >= tokens.length) return;
        var token = tokens[idx];
        var tok = el("div", { class: "sort-token", role: "button", title: "Tap to hear" }, el("span", {}, token.t));
        tok.addEventListener("click", function (e) { if (e.target === tok || e.target.tagName === "SPAN") api.speak(token.t); });
        current.appendChild(tok);
        api.speak(token.t);
      }
      function binFor(cat) { return cat === "A" ? binA : binB; }
      function place(cat, node) {
        if (idx >= tokens.length) return;
        var token = tokens[idx];
        if (cat === token.cat) {
          var chip = el("div", { class: "sort-token" }, el("span", {}, token.t));
          binFor(token.cat).items.appendChild(chip); idx++;
          if (idx >= tokens.length) { current.innerHTML = ""; setTimeout(function () { api.finish(); }, FAST ? 0 : 250); }
          else renderCurrent();
        } else { node.classList.add("wrong"); api.addMistake(); api.wrong(); setTimeout(function () { node.classList.remove("wrong"); }, 450); }
      }
      renderCurrent();
      api.registerSolver(function () { var g = 0; while (idx < tokens.length && g < 60) { binFor(tokens[idx].cat).node.click(); g++; } });
      api.registerWrongSolver(function () { if (idx < tokens.length) binFor(tokens[idx].cat === "A" ? "B" : "A").node.click(); });
    },

    say_it: function (host, api) {
      var item = api.pick(api.pool);
      api.setInstruction("🎤 Tap the mic and say the word");
      host.appendChild(api.flashcard(item, { label: true, spokenText: item.word }));
      var heard = el("div", { class: "heard" }, "");
      var mic = el("button", { class: "mic-btn", "aria-label": "Record" }, "🎤");
      host.appendChild(mic); host.appendChild(heard);

      var done = false;
      function succeed() { if (done) return; done = true; mic.classList.remove("recording"); api.finish(); }
      var SR = window.SpeechRecognition || window.webkitSpeechRecognition, tries = 0;
      mic.addEventListener("click", function () {
        if (done) return;
        api.speak(item.word); heard.textContent = "Listening..."; mic.classList.add("recording");
        if (!SR) { setTimeout(function () { heard.textContent = "Nice try! 👍"; succeed(); }, 900); return; }
        var rec; try { rec = new SR(); } catch (e) { setTimeout(succeed, 600); return; }
        rec.lang = "en-US"; rec.maxAlternatives = 3; rec.interimResults = false; var got = false;
        rec.onresult = function (ev) {
          got = true; var said = "";
          for (var i = 0; i < ev.results.length; i++) said += ev.results[i][0].transcript + " ";
          heard.textContent = "I heard: " + said.trim();
          if (said.toLowerCase().indexOf(item.word.toLowerCase()) >= 0) succeed();
          else { tries++; if (tries >= 2) { heard.textContent += "  (Great effort!)"; succeed(); } else { api.addMistake(); api.wrong(); } mic.classList.remove("recording"); }
        };
        rec.onerror = function () { mic.classList.remove("recording"); setTimeout(function () { heard.textContent = "Good try! 👍"; succeed(); }, 400); };
        rec.onend = function () { mic.classList.remove("recording"); if (!got) setTimeout(function () { if (!done) succeed(); }, 300); };
        try { rec.start(); } catch (e) { setTimeout(succeed, 600); }
        setTimeout(function () { if (!done && !got) { try { rec.stop(); } catch (e) { } } }, 3500);
      });
      api.registerSolver(function () { succeed(); });
    },

    build_sentence: function (host, api) {
      var sentence = api.pick(api.sentences);
      var words = sentence.replace(/[.?!]$/, "").split(/\s+/);
      var punct = (sentence.match(/[.?!]$/) || ["."])[0];
      api.setInstruction("🧩 Tap the words in order");
      host.appendChild(el("div", { class: "instruction" }, api.speakerPrompt(sentence), el("span", {}, " Listen to the sentence")));

      var slotRow = el("div", { class: "slot-row" }), slots = [];
      words.forEach(function () { var sl = el("div", { class: "slot" }, ""); slotRow.appendChild(sl); slots.push({ node: sl }); });
      slotRow.appendChild(el("div", { class: "slot", style: { border: "none", background: "transparent", minWidth: "auto" } }, punct));
      host.appendChild(slotRow);

      var tileRow = el("div", { class: "tile-row" }); host.appendChild(tileRow);
      var tiles = api.shuffle(words.map(function (w, i) { return { w: w, i: i }; })), filled = 0;
      var activeSlot = null;
      function countFilled() {
        filled = slots.reduce(function (n, sl) { return n + (sl.tileRef ? 1 : 0); }, 0);
      }
      function selectSlot(index) {
        activeSlot = index;
        slots.forEach(function (sl, i) { sl.node.classList.toggle("active", i === index); });
      }
      function resetBoard() {
        slots.forEach(function (sl) {
          if (sl.tileRef) { sl.tileRef.classList.remove("used"); sl.tileRef = null; }
          sl.node.textContent = ""; sl.node.classList.remove("filled", "bad", "ok", "active"); sl.word = null;
        });
        activeSlot = null; filled = 0;
      }
      tiles.forEach(function (t) {
        var tile = el("button", { class: "tile" }, t.w); t.tile = tile;
        tile.addEventListener("click", function () {
          if (tile.classList.contains("used")) return;
          var targetIndex = null;
          if (activeSlot != null && !slots[activeSlot].tileRef) targetIndex = activeSlot;
          else {
            for (var i = 0; i < slots.length; i++) {
              if (!slots[i].tileRef) { targetIndex = i; break; }
            }
          }
          if (targetIndex == null) return;
          var sl = slots[targetIndex];
          sl.node.textContent = t.w; sl.node.classList.add("filled");
          sl.tileRef = tile; sl.word = t.w; tile.classList.add("used");
          selectSlot(null);
          countFilled();
          if (filled === slots.length) check();
        });
        tileRow.appendChild(tile);
      });
      slots.forEach(function (sl, i) {
        sl.node.addEventListener("click", function () {
          if (!sl.tileRef) {
            selectSlot(i);
            return;
          }
          sl.tileRef.classList.remove("used"); sl.tileRef = null;
          sl.node.textContent = ""; sl.node.classList.remove("filled", "bad", "ok", "active"); sl.word = null;
          if (activeSlot === i) activeSlot = null;
          countFilled();
        });
      });
      function check() {
        var ok = slots.every(function (sl, i) { return sl.word === words[i]; });
        if (ok) { slots.forEach(function (sl) { sl.node.classList.add("ok"); }); api.speak(sentence); setTimeout(function () { api.finish(); }, FAST ? 0 : 350); }
        else {
          slots.forEach(function (sl, i) { sl.node.classList.remove("bad", "ok"); if (sl.word != null && sl.word === words[i]) sl.node.classList.add("ok"); else if (sl.word != null) sl.node.classList.add("bad"); }); api.addMistake(); api.wrong();
        }
      }
      function clickInOrder() {
        resetBoard();
        for (var i = 0; i < words.length; i++) {
          for (var j = 0; j < tiles.length; j++) if (tiles[j].w === words[i] && !tiles[j].tile.classList.contains("used")) { tiles[j].tile.click(); break; }
        }
      }
      api.registerSolver(function () {
        var wrongTile = tiles.filter(function (t) { return t.w !== words[0] && !t.tile.classList.contains("used"); })[0];
        if (wrongTile) { wrongTile.tile.click(); setTimeout(function () { resetBoard(); clickInOrder(); }, 0); }
        else clickInOrder();
      });
      api.registerWrongSolver(function () {
        var wrongTile = tiles.filter(function (t) { return t.w !== words[0] && !t.tile.classList.contains("used"); })[0];
        if (wrongTile) wrongTile.tile.click();
      });
    },

    spell_it: function (host, api) {
      var used = api.session && api.session.spellWordsUsed ? api.session.spellWordsUsed : [];
      var choices = api.pool.filter(function (it) { return /^[a-z]+$/i.test(it.word) && it.word.length >= 3 && it.word.length <= 7; });
      var available = choices.filter(function (it) { return used.indexOf(String(it.word).toLowerCase()) < 0; });
      var item = api.pick(available.length ? available : choices.length ? choices : api.pool);
      var word = item.word.replace(/[^a-z]/gi, "");
      api.markSpellWordUsed(item.word);
      api.setInstruction("🔤 Tap the letters to spell it");
      host.appendChild(api.flashcard(item, { speak: true, spokenText: item.word }));

      var slotRow = el("div", { class: "slot-row" }), slots = [];
      for (var i = 0; i < word.length; i++) {
        var sl = el("div", { class: "slot" }, "");
        slots.push({ node: sl, ch: null, tileRef: null, locked: false });
        slotRow.appendChild(sl);
      }
      host.appendChild(slotRow);

      var tileRow = el("div", { class: "tile-row letters" }); host.appendChild(tileRow);
      var letters = api.shuffle(word.split("").map(function (c, i) { return { c: c, i: i }; }));

      function firstEmpty() { for (var i = 0; i < slots.length; i++) if (slots[i].ch == null && !slots[i].locked) return slots[i]; return null; }
      function isFull() { return slots.every(function (s) { return s.ch != null; }); }

      letters.forEach(function (L) {
        var tile = el("button", { class: "tile" }, L.c); L.tile = tile;
        tile.addEventListener("click", function () {
          if (tile.classList.contains("used")) return;
          var sl = firstEmpty();
          if (!sl) return;
          sl.node.textContent = L.c; sl.node.classList.add("filled");
          sl.ch = L.c; sl.tileRef = tile; tile.classList.add("used");
          if (isFull()) check();
        });
        tileRow.appendChild(tile);
      });
      // tap ANY placed (non-locked) letter — middle or last — to send it back
      slots.forEach(function (sl) {
        sl.node.addEventListener("click", function () {
          if (sl.locked || !sl.tileRef) return;
          sl.tileRef.classList.remove("used");
          sl.node.textContent = ""; sl.node.classList.remove("filled", "bad");
          sl.tileRef = null; sl.ch = null;
        });
      });
      function check() {
        var allCorrect = true;
        slots.forEach(function (s, i) {
          if (s.ch && s.ch.toLowerCase() === word[i].toLowerCase()) {
            s.locked = true; s.node.classList.remove("bad"); s.node.classList.add("ok");   // right spot -> lock green
          } else { allCorrect = false; }
        });
        if (allCorrect) { api.speak(word); setTimeout(function () { api.finish(); }, FAST ? 0 : 350); return; }
        // keep the green letters; flash + clear ONLY the wrong ones for another try
        api.addMistake(); api.wrong();
        slots.forEach(function (s) { if (!s.locked) s.node.classList.add("bad"); });
        setTimeout(function () {
          slots.forEach(function (s) {
            if (s.locked) return;
            s.node.classList.remove("bad", "filled"); s.node.textContent = "";
            if (s.tileRef) s.tileRef.classList.remove("used");
            s.tileRef = null; s.ch = null;
          });
        }, FAST ? 0 : 700);
      }
      function spellCorrect() {
        for (var i = 0; i < word.length; i++) {
          if (slots[i].ch != null) continue;
          var need = word[i].toLowerCase();
          for (var j = 0; j < letters.length; j++)
            if (letters[j].c.toLowerCase() === need && !letters[j].tile.classList.contains("used")) { letters[j].tile.click(); break; }
        }
      }
      api.registerSolver(spellCorrect);
    }
  };

  /* ========================= 10. Test hooks =========================== */
  window.GilorTest = {
    ready: false,
    state: function () {
      var s = App.session, prof = currentProfile() || {};
      var screen = "unknown";
      if ($(".login-card")) screen = "login";
      else if ($(".rank-list")) screen = "ranks";
      else if ($(".world-map")) screen = "home";
      else if ($(".summary")) screen = "summary";
      else if ($("#play-host")) screen = "game";
      return {
        screen: screen, user: currentUsername(),
        totalStars: prof.stars || 0, best: prof.best || 0,
        unlocked: prof.unlocked || 0, mastered: masteredCount(prof),
        levelScores: prof.levelScores || {},
        totalLevels: TOTAL_LEVELS,
        level: s ? s.level.id : null, levelIndex: s ? s.level.index : null,
        gameIndex: s ? s.index : null, gameType: s ? s.order[s.index] : null,
        sessionPoints: s ? Math.max(0, 100 - s.mistakes) : null, awaitingNext: App.awaitingNext,
        results: s ? s.results.slice() : []
      };
    },
    login: function (u, p) {
      var profiles = getProfiles();
      if (!profiles[u]) { profiles[u] = normalize({ pass: obfuscate(p) }); saveProfiles(profiles); }
      else if (profiles[u].pass !== obfuscate(p)) return false;
      setCookie(CURRENT_KEY, u, 365); App.renderHome(); return true;
    },
    startLevel: function (ref) { return App.startSession(ref); },   // false if locked
    // Solve the current game; pass a number to first make that many wrong attempts.
    solveCurrent: function (mistakes) {
      mistakes = mistakes || 0;
      for (var i = 0; i < mistakes; i++) { if (App._wrongSolver) App._wrongSolver(); }
      if (App._solver) { App._solver(); return true; }
      return false;
    },
    next: function () { App.next(); },
    openRanks: function () { App.renderRanks(); },
    goHome: function () { App.renderHome(); },
    logout: function () { App.logout(); },
    setFast: function (v) { FAST = !!v; },
    // Speak one phrase and resolve when it finishes (lets the E2E play words one
    // at a time, fully audible, and confirm each actually spoke).
    say: function (text) {
      return new Promise(function (resolve) { Audio.speak(text, { onend: function () { resolve(true); } }); });
    },
    // Play the whole current session in-browser (fast). Resolves with the outcome.
    // `mistakes` wrong attempts are made on each game that supports them.
    playSession: function (mistakes) {
      mistakes = mistakes || 0;
      return new Promise(function (resolve) {
        var types = [], guard = 0;
        function stepOnce() {
          if (++guard > 400) { resolve({ error: "runaway", types: types }); return; }
          var st = window.GilorTest.state();
          if (st.screen === "summary") {
            var minStars = (st.results || []).reduce(function (m, r) { return Math.min(m, r.stars); }, 3);
            resolve({ score: st.sessionPoints, types: types, unlocked: st.unlocked, minStars: minStars, results: st.results });
            return;
          }
          if (st.screen !== "game") { resolve({ error: "not-in-game:" + st.screen, types: types }); return; }
          types.push(st.gameType);
          if (!window.GilorTest.solveCurrent(mistakes)) { resolve({ error: "no-solver:" + st.gameType, types: types }); return; }
          var tries = 0;
          (function waitFinish() {
            if (App.awaitingNext) { window.GilorTest.next(); setTimeout(stepOnce, 0); return; }
            if (++tries > 150) { resolve({ error: "no-finish:" + st.gameType, types: types }); return; }
            setTimeout(waitFinish, 20);
          })();
        }
        stepOnce();
      });
    }
  };

  /* ============================== boot ================================ */
  if (document.readyState === "loading")
    document.addEventListener("DOMContentLoaded", function () { App.start(); });
  else App.start();
  window.MagicAcademy = App;
})();
