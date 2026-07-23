# Review & Fix Summary — Levels 101–300 (Grammar)

**Date:** 2026-07-22
**Scope:** Levels 101–300 (global index 100–299). Levels 1–100 (vocabulary) were
left unchanged, as requested.
**Goal:** Make levels 101–300 teach English **grammar** correctly and be **fun** —
so a child practices reading, listening, speaking and understanding, and never
learns wrong English.

Every level was reviewed both by reading the source/data **and** by playing it
end‑to‑end in a real browser with Playwright (headed and headless).

---

## 1. What was wrong (before)

### Levels 201–300 were effectively broken
- They had **no grammar data at all**. Because their game line‑up was 4 grammar
  games that read from an (empty) grammar block, **3 of the 4 games rendered
  empty and auto‑passed** — the child tapped nothing and "won". They taught
  nothing.
- Their example sentences were auto‑generated nonsense that **teaches wrong
  English**, e.g. *"This is a played."*, *"I am sing."*, *"This is an if."*,
  *"I like the seen."*

### Levels 101–200 were monotonous and sometimes incorrect
- Every level played the **same 4 tap‑only games** (`Choose the Word`,
  `Change the Word`, `Fix It`, `Sort It`) — **no speaking, no listening, no
  reading/sentence‑building** and only 4 games instead of 10. Repetitive and not fun.
- Template generation produced **real grammar errors**, for example:
  - L108 "Count the Bots" taught *"This is a two."* and *"one two → twos"*.
  - L117 "Grandma's Chip" (irregular plurals) taught **"womans / foots / mouses"
    as correct**, and its actual exercises were about *am/is/are*, not plurals.
  - L187 "Slime Maker" (nationalities) generated *"Spainer"*, *"more France"*,
    *"Israeler"*.
  - Stray nonsense sentences such as *"Can you bag?"*, *"Can you desk?"*.
- Sort games were unbalanced (e.g. 5 tokens in one bin, 1 in the other).

---

## 2. What was changed

### A. New grammar games (engine — `app.js`)
Added and registered new mini‑games (you approved adding games):

| Game | id | What the child does | Teaches |
|------|----|--------------------|---------|
| **Find the Mistake** | `tap_word` | One sentence is shown; tap the **one wrong word** (it corrects on tap) | noticing errors precisely (spelling, agreement, capital letters) |
| **Question & Answer** | `phrase_pair` | Match each **question to its correct answer** | conversation, short answers, tag responses |
| **Listen & Choose** | `listen_sentence` | Hear a full sentence, then **tap the sentence you heard** (no microphone) | listening comprehension of whole grammatical sentences |

> The original mic **Say It** game was **removed** from the grammar levels — browser
> speech recognition is unreliable — and replaced by **Listen & Choose**, which
> practices the same "hear English" skill but only needs taps.

- `tap_word` derives its content from the level's existing right/wrong pairs, so
  it needs no extra data. It finds the single differing word (case‑insensitive,
  then case‑sensitive so *"dan → Dan"* capitalization also works) and falls back
  to *Fix It* if a level has no clean single‑word difference.
- `phrase_pair` de‑duplicates questions/answers at runtime so a match is never
  ambiguous.
- CSS added for both (wrapping phrase cards, green/red word chips).

### B. A rich, varied 10‑game recipe for every grammar level (`build_assets.py`)
Grammar levels now play **10 different games** each (order shuffled), so the
child **hears, reads, speaks and understands** every structure:

```
Listen & Read → Choose the Word → Build a Sentence → Sort by Rule → Change the Word →
Fix It → Find the Mistake → Question & Answer → Listen & Choose → Spell It
```

- Hearing: every game speaks; `Listen & Read` (word) and `Listen & Choose`
  (whole sentence) are dedicated listening games.
- Reading: `Build a Sentence`, `Spell It`, `Choose the Word`, `Find the Mistake`.
- Grammar/understanding: the five grammar games above.

### C. All 200 grammar levels re‑authored by hand (correct English)
The fragile templates were replaced with **explicit, hand‑written content** for
every level, stored in readable per‑world files:

- `grammar_helpers.py` — small authoring helpers. The correct answer is given as
  a **string** (not an index), and the helpers assert it is one of the options —
  so an answer can never silently point at the wrong choice. They also reject
  duplicate options and unbalanced sort bins at build time.
- `grammar_content.py` — assembles the 20 grammar worlds.
- `w02.py … w20.py` — one file per world (10 levels each).

Each level supplies: 6 topic items (for hear/say/spell), 5–6 short **correct**
example sentences, and grammar blocks for gap‑fill, transform, fix, sort, and
question/answer.

**Coverage (grammar arc):**

| Levels | World | Grammar focus |
|--------|-------|---------------|
| 101–110 | Digital Classroom | this/that/these/those, a/an, plurals |
| 111–120 | Family & Feelings | verb *to be*, negatives, questions, **irregular plurals (men/feet/children…)** |
| 121–130 | Activities | can / can't (+ base verb) |
| 131–140 | My Things | have got / has got, possessives (my/’s/mine) |
| 141–150 | Food I Like | present simple like/likes, do/does, object pronouns |
| 151–160 | Daily Routine | present simple, he/she ‑s, telling time, frequency |
| 161–170 | Activities I Love | present continuous, ‑ing spelling |
| 171–180 | How Much/Many | countable/uncountable, some/any, would like, prepositions |
| 181–190 | Let's Compare | comparatives (‑er / more / **better, worse**), **nationalities (Spanish/French…)** |
| 191–200 | Places & Past | was/were, there was/were, directions, past time words |
| 201–210 | Tense Trek | present vs continuous, past regular/**irregular**, perfect & continuous tenses, will, going to |
| 211–220 | Modal Mountain | can/could, may/might, must/have to, should, used to, permission, review |
| 221–230 | Conditional Cove | zero/first/second/third conditionals (correct *were* / *would have + participle*) |
| 231–240 | Passive Place | passive voice (be/get + correct participle), by‑agent, active↔passive |
| 241–250 | Speech Street | reported speech, relative clauses, tag questions, objects, gerunds/infinitives |
| 251–260 | Structure Station | phrasal verbs (get/take/put/make/look), idioms, collocations, linking words, prepositions of time |
| 261–270 | Quantifier Quay | prepositions of place/movement, directions, comparisons, routines, health, food, recipes |
| 271–280 | Polite Plaza | shopping, money, jobs (a/an), certainty (must/might be), preferences, permission, offers, advice |
| 281–290 | Everyday Express | apologizing, help, telephone, email, small talk, describing people, family, travel, hotel, directions |
| 291–300 | Big Idea Boulevard | weather, seasons, sports (play/go/do), hobbies, music, animals, environment (should/must), technology, science, feelings |

### D. Cleanup
- Removed the dead, buggy template generators (`make_grammar`, `grammar_sort`,
  `GRAMMAR_WORLDS`, `ADVANCED_WORLDS`) from `build_assets.py` so the old
  "womans / Spainer" logic can never be re‑enabled by accident.

### E. Follow‑up fixes (after the Level 101 manual test)
- **Removed the mic game** and replaced it with **Listen & Choose** (see A).
- **Clearer "Change the Word" prompts:** the plural prompt `one pen ->` was
  ambiguous (the options even include the base word). Changed to
  `one pen -> many...?` across **all 144** plural prompts in every level, plus the
  three counting prompts (`one robot -> two...?` etc.).
- **Centered options:** "Choose the Word" with 2 or 3 answers used a 4‑column
  grid, so the options hugged the left. `singleChoice` now picks a 2‑ or 3‑column
  grid so 2–3 options are centered.

---

## 3. How it was verified

- **Static validator** over all 200 levels: grammar block completeness, answer‑in‑options,
  balanced sort bins, sentence punctuation, and an a/an‑agreement check → **0 errors**.
- **Full Playwright sweep of all 300 levels**: every level plays all **10 games**,
  each is solvable, and a clean run scores **100 / 3 stars** → **300 / 300 clean,
  0 anomalies**. Levels 1–100 confirmed unaffected.
- **Full human read‑through** of all 200 grammar levels' sentences, questions,
  answers and options for grammatical correctness.
- **Headed playthroughs** (visible browser) of basic and advanced levels, plus
  screenshots confirming the games look right and teach the point (e.g. passive
  *"The cake was **ate**"* → tap to fix to *eaten*; second conditional *"If she
  **were** here"*; tag question matching).

---

## 4. Rebuilding / regenerating

Content is generated from source — after editing any `w*.py` / `grammar_content.py`:

```bash
python3 build_assets.py     # regenerates content.json, data.js and images/*.svg
```

To play/verify locally:

```bash
python3 -m http.server 8000   # then open http://localhost:8000/
```

**Audio note:** the game speaks every word/sentence with the browser's Web Speech
API (American English) — this already covers all the new text, so no audio step
is required. (If you later want pre‑recorded clips, `build_audio.py` on macOS can
generate them; it will pick up the new strings automatically.)

## 5. Files changed / added
- `app.js` — added `tap_word` and `phrase_pair` games (+ solvers, CSS in `style.css`).
- `build_assets.py` — new 10‑game grammar recipe; registers the new games + `say_it`;
  consumes hand‑authored grammar content; removed dead generators.
- `grammar_helpers.py` *(new)* — safe authoring helpers.
- `grammar_content.py` *(new)* — assembles the 20 grammar worlds (World 1 inline).
- `w02.py … w20.py` *(new)* — hand‑authored levels 111–300.
- `content.json`, `data.js`, `images/*.svg` — regenerated (300 levels).
- `style.css` — styles for the two new games.
