# 🚀 Magic Academy: English Quest

A colorful, fully-working web game that helps a young beginner (built for
8-year-old **Tzofia**, Novakid **Level 2 – Starters**) practice English through
**100 levels** of 10 different mini-games each. Inspired by the Novakid
"Magic Academy" screens and curriculum.

Everything runs in the browser — **no build step, no server-side code, no
accounts on any server.** Just static files in one folder.

---

## ▶️ How to play (run it)

The game uses **cookies**, so it must be opened over `http://` (not by
double-clicking the file). Start a tiny local server from this folder:

```bash
cd Gilor
python3 -m http.server 8000
```

Then open **http://localhost:8000/** in Chrome, Safari or Edge.

1. Type a **name** and a **secret word** (password) — this creates the player.
2. On the **world map**, tap **▶ Play Level 1** (or the highlighted level).
3. Play the 10 games. **Tap any picture to hear its word.** Use 🔊 to hear
   the prompt, 🔁 to repeat the instruction, 🚩 to skip.
4. See your score **out of 100** and your total ⭐ stars, which are saved.
   Score **95 or more** to **unlock the next level**.
5. Tap **🏆 Ranks** to see how every player compares.

> 🔈 **Turn the sound on.** All words, sentences and praise are spoken in an
> **American (en-US) accent** by the browser's built-in speech engine.

---

## 🎮 The 10 game types

| # | Game | What the child does |
|---|------|---------------------|
| 1 | **Listen & Find** | Hear a word → tap the matching picture |
| 2 | **What is it?** | See a picture → tap the matching word |
| 3 | **Find the Sound** | See a picture → tap the speaker that says it |
| 4 | **Match It** | Match each picture to its spoken word |
| 5 | **Sort It** | Drop each word into the right category box |
| 6 | **Say It** | Tap the mic and say the word (speaking practice) |
| 7 | **Build a Sentence** | Tap word tiles in the correct order |
| 8 | **Spell It** | Tap letters to spell the word |
| 9 | **Yes or No?** | Does the word match the picture? ✅ / ❌ |
| 10 | **Listen & Read** | Hear a word → tap the matching written word |

A **level = 10 games** (one of each type, shuffled) drawn from that level's
topic. **Grading is simple: a level starts at 100 and loses 1 point for every
wrong tap/answer** (skipping a game 🚩 costs 10). So making **more than 5
mistakes** in a level drops you below **95** and the next level stays locked.
Each game also shows **1–3 ⭐** (based on its own mistakes) and stars are
cumulative per player, forever.

A couple of kid-friendly touches:

* **Spell It** locks each correctly-placed letter **green** and only clears the
  wrong ones for another try — and you can pull **any** letter back out (not
  just the last one), including a middle letter.
* **Sort It** puts a 🔊 speaker on each group box so the child can hear the
  group's name.

---

## 🗺️ 100 levels, worlds & unlocking

The 100 levels are grouped into six **worlds** that mirror the real Novakid
ladder, each covering a topic extracted from the reference curriculum:

| World | Feel | Example topics |
|-------|------|----------------|
| **Pre-K Planet** | first tiny words | Colors, Numbers, Shapes, Pets, Family |
| **Juniors Jungle** | lots of first words | Wild/Sea animals, Food, Clothes, Weather |
| **Starters Station** | Tzofia's Magic Academy | Classroom, Feelings, Daily routine, Transport, Opposites |
| **Movers Mountain** | bigger ideas | Jobs, Sports, Space, House rooms, Shopping |
| **Flyers Forest** | clever words | Reptiles, Technology, School subjects, Holidays |
| **Explorers Galaxy** | master challenges | Tools, Deep space, Dinosaurs, Fantasy |

**Unlocking:** every level starts **locked** except the first. Score **≥ 95**
on a level to unlock the next one. You can replay any unlocked level to improve
your score and push forward. The home screen shows the whole map: 🔒 locked,
✓ mastered (green), and the current level highlighted.

## 🏆 Rank board

Tap **🏆 Ranks** to see every player on this device ranked by total ⭐ stars
(then levels mastered 🏅, then best score 🎯). The signed-in player is
highlighted, and the top three get 🥇🥈🥉.

---

## 🗂️ Project structure

```
Gilor/
├── index.html          # app shell
├── style.css           # all styling (the chunky cartoon look)
├── app.js              # game engine, auth, scoring, persistence, 10 games
├── data.js             # window.GAME_DATA  (loaded by the browser)
├── content.json        # the same curriculum data, as a clean JSON file
├── images/             # one small colorful <slug>.svg picture per word (~470)
├── audio/              # ~980 pre-recorded .m4a clips (words, sentences, praise…)
├── audio_manifest.js   # window.AUDIO_MANIFEST — text -> audio file
├── build_assets.py     # regenerates content.json, data.js and images/
├── build_audio.py      # regenerates audio/*.m4a + audio_manifest.js (macOS)
├── test_e2e.py         # Playwright end-to-end test
├── requirements.txt    # test dependencies
├── levels/             # (your reference sketches — curriculum)
└── screenshots examples/  # (your reference sketches — game screens)
```

### Curriculum / difficulty tiers
`content.json` (and the identical `window.GAME_DATA` in `data.js`) holds **100
levels** across six worlds (see the map above). Every level has a `world`,
a global `index` (for unlock order), a `name` (its topic), a `color`, a list of
vocabulary `items` (each with `word`, `emoji`, `slug`, `image`), and a few
example `sentences` used by the sentence-builder game.

To change or add content, edit `build_assets.py` and re-run it:

```bash
python3 build_assets.py     # rewrites content.json, data.js and images/*.svg
```

---

## 🎨 & 🔊 Design decisions (media assets)

Two deliberate, robust choices so the game **always works offline and never
shows a broken asset** — while still meeting every requirement:

* **Pictures** are delivered as small, colorful **SVG files** in `images/`
  (real files, referenced by the data's `image` field). Each renders a themed
  card with the matching emoji, so they are crisp at any size, tiny, and
  license-free. If a file is ever missing, the app instantly falls back to a
  live emoji — pictures can't break. Swap any SVG for a photo whenever you like.
* **Audio (American accent)** is served from **pre-recorded files in `./audio`**
  (≈980 small `.m4a` clips) so it **does not depend on the browser's speech
  engine** — every word, sentence, praise line ("Very good!", "Well done!") and
  feedback line plays from a real recording. Getting a **95** or finishing a
  level plays a **random praise** word. The clips are generated on macOS by
  `build_audio.py` (voice *Samantha*, en-US); the browser's Web Speech API is
  only a last-resort fallback if a clip is ever missing.

  Regenerate the audio pack any time (after editing content):

  ```bash
  python3 build_assets.py     # data + images
  python3 build_audio.py      # ./audio/*.m4a  + audio_manifest.js  (macOS)
  ```

## 🔐 Login & persistence

* Login creates/loads a player stored in a cookie (`mae_profiles`). The signed-in
  player is remembered in `mae_current`, so the game reopens straight to *Home*.
* Cumulative stars, best score, session count, the highest **unlocked** level
  and every **per-level best score** are saved per player and **persist across
  sessions** (365-day cookies) — progress and the world map survive a reload.
* The password is only lightly obfuscated (base64) — this is a kids' game on a
  personal device, **not** real security. Don't reuse a sensitive password.

---

## ✅ End-to-end test (Playwright)

`test_e2e.py` launches a **visible (headed)** Chromium, serves the folder, and
plays the **entire game — all 100 levels, start to finish**. Every run
registers a **brand-new user whose name contains the date & time**
(`kid_YYYYMMDD_HHMMSS`), so runs never collide.

It verifies, for **every** level:

* the level is unlocked and its **ten games all render and are solvable**
  (all 10 game types present each session);
* a **WRONG run** (deliberate wrong answers) scores **< 95**, loses stars, and
  the next level **stays locked**;
* a **CORRECT run** scores **100** and **unlocks the next level** — then it
  moves on, sweeping right through to Level 100.

Plus, on Level 1 in detail: pictures load, the **sound buttons speak in en-US**,
and **"What is it?" answers on a word tap** (no ANSWER button). It finishes by
checking the **rank board** ordering/highlight and that **all progress persists**
across a page reload. A screenshot lands in `test-artifacts/e2e-summary.png`.

> The sweep uses a hidden `fast` automation mode (skips animations/audio) so 200
> game sessions finish in a few minutes; Level 1's detailed pass runs at normal
> speed so you can see and hear it.

```bash
pip install -r requirements.txt
python -m playwright install chromium
python test_e2e.py          # prints PASS/FAIL, exits non-zero on failure
# or:  pytest test_e2e.py
```

A screenshot of the finished run is saved to `test-artifacts/e2e-summary.png`.
