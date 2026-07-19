# Magic Academy — Levels 101–200: Grammar Quest (Design & Implementation Plan)

> **Purpose.** This is a hand-off spec for an implementing agent. It describes how to
> add **100 new levels (101–200) that teach English grammar** to the *existing* game
> (same `index.html`, same engine, same look & feel), following the Level 2 "Starters"
> curriculum captured in **`level.md`**. Read `level.md` and `README.md` first; this
> document assumes both.
>
> The first 100 levels (0–99) teach **vocabulary**. Levels 101–200 teach **grammar**,
> reusing the same 10-mini-game session, the same scoring, the same unlock chain, and
> the same asset pipeline — plus **4 new grammar mini-games** and one small per-level
> data field. Nothing about levels 0–99 changes.

---

## 0. TL;DR for the implementer

You will:

1. **Add 10 new "worlds" (100 levels) to `build_assets.py`** — one world per Unit 1–10
   of `level.md`. Each level carries the usual `items`/`sentences` **plus a new
   `grammar` block** and an explicit `gameTypes` list.
2. **Add 4 new mini-games to `app.js`**: `pick_word_gap`, `transform`, `fix_sentence`,
   `sort_rule` (Sort It generalised). Register them in `GAME_TYPES` too.
3. **Add one tiny engine tweak**: let a level choose its own game line-up
   (`level.gameTypes`), falling back to all types when absent.
4. **Extend the two build scripts** to emit the new data + audio for the new text.
5. **Extend `test_e2e.py`** only by making sure every new game registers a solver (the
   sweep already plays "one of each game type" per level).

Everything else — the world map, 🔒/✓ unlocking, ranks, persistence, stars, grading —
**already scales to 200 levels with no code change** because it is driven by
`DATA.levels` (`TOTAL_LEVELS = DATA.levels.length`) grouped by `worldIndex`.

---

## 1. Design goals

- **Learn grammar by playing, not by reading rules.** No lecture screens. A child
  masters "These are apples" by *building* it, *fixing* it, *sorting* it, and *saying*
  it — the same tactile pattern that made the vocab levels work.
- **Faithful to `level.md`.** The 10 grammar worlds map 1-to-1 onto Units 1–10 of the
  Level 2 Starters ladder, and the grammar target of each world is exactly that unit's
  grammar focus (this/these → to be → can → have got → present simple → daily routine →
  present continuous → quantity → comparatives → was/were).
- **Same feel as levels 0–99.** 10 mini-games per level, start at 100, −1 per wrong
  tap, −10 per skip, **≥ 95 unlocks the next**, 1–3 ⭐ per game, cumulative stars.
- **Spiral + scaffold.** Each world runs *introduce → contrast → question/negative →
  phonics → mixed review*. Vocabulary from the matching unit is reused so the child
  keeps meeting known words while the *structure* is new.
- **Graceful, offline, unbreakable.** Same guarantees as today: SVG pictures fall back
  to a live emoji, audio falls back to Web Speech. New grammar data must never let a
  game render with fewer than its required options.

---

## 2. How the current game works (the contract you must fit)

**Single source of truth:** `build_assets.py` → writes `content.json`, `data.js`
(`window.GAME_DATA`), and `images/<slug>.svg`. `build_audio.py` → reads `content.json`,
records `audio/*.m4a`, writes `audio_manifest.js`.

**A level object** (see `content.json`) has:

```jsonc
{
  "id": "L42", "index": 42,               // index = global unlock order
  "world": "…", "worldSubtitle": "…", "worldIndex": 3,
  "name": "Topic",                        // spoken by Sort It group boxes
  "category": "L42",                      // unique tag (Sort It uses it)
  "color": "#BFE2FF",
  "items": [ { "word":"cat","emoji":"🐱","slug":"cat","image":"images/cat.svg","color":"…" }, … ],
  "sentences": [ "This is my cat.", … ]   // used by Build a Sentence
}
```

**The engine** (`app.js`): `startSession(ref)` builds
`session = { level, pool: level.items, sentences: level.sentences, order: shuffle(gameTypeIds), … }`
then `renderGame()` calls `GAMES[typeId](host, api)` for each of the 10 games.

Each game receives an **`api`** with the useful helpers:
`api.pool` (items), `api.sentences`, `api.level` (whole level → **`api.level.grammar`**),
`api.allLevels`, `api.el`, `api.pick`, `api.shuffle`, `api.sample`, `api.distractors`,
`api.picNode`, `api.flashcard`, `api.speakerPrompt`, `api.speak`, `api.setInstruction`,
`api.addMistake`, `api.wrong`, `api.finish`, `api.registerSolver`, `api.registerWrongSolver`.

There is a shared multiple-choice helper you should reuse for the new games:

```js
singleChoice(host, api, {
  promptNode,            // a DOM node shown above the options
  twoUp,                 // bool: 2-column layout
  options: [ {…}, … ],   // your option data objects
  correct: <index>,      // index of the right option
  instant,               // bool: click = commit (no ANSWER button)
  onSelect: function (d) {},          // e.g. speak the tapped option
  renderOption: function (d, i) { return <node>; }
});
// singleChoice auto-registers a correct solver (clicks `correct`) AND a wrong solver.
```

**Grading & stars** (do not change): a game reports mistakes via `api.addMistake()`;
`completeGame` awards 3⭐ (0 mistakes) / 2⭐ (≤2) / 1⭐ (else) / 0⭐ (skipped) and the
level's running score is `100 − mistakes − 10·skips`. **≥ 95 unlocks the next index.**

**Why 200 levels "just work":** `renderHome()` groups `DATA.levels` by `worldIndex`
and draws every level; unlock test is `lv.index <= unlocked`; `startSession` chains on
`level.index > prof.unlocked`. Adding levels 100–199 with `worldIndex` 6–15 extends the
map and the unlock chain automatically. (Only cosmetic note: the map gets longer — it
already scrolls.)

---

## 3. The 100-level grammar map (Worlds 11–20 = Units 1–10)

Global `index` 100–199 → level ids **L100–L199**, shown to the player as **Levels
101–200**. Ten worlds of ten levels. Each world = one `level.md` unit; each world's
10 levels follow that unit's lesson flow (4 quests → review → extra practice), ending
in a mixed **Unit Review** mastery level. Vocabulary `items` come from the unit's topic
(reuse existing slugs/emojis where possible so no new art is needed).

Legend for **"Featured game"** = the grammar mini-game that carries the new structure
(every level still plays 10 games; see §5 for the full recipe).

### World 11 — Unit 1 · Digital Classroom  (L100–L109 → "Level 101–110")
*Grammar arc: `this/that/these/those`, `a/an`, singular↔plural, "What is this?"*
Vocab: classroom objects (pen, book, desk, bag, ruler, tablet, board, chair).

| Lvl | id | Quest / focus | Grammar target | Example |
|----|-----|----|----|----|
|101|L100|The Alien Princess|`This is a …` (singular + **a**)|"This is a pen."|
|102|L101|A or An?|**a** vs **an**|"This is an apple."|
|103|L102|Through the Portal|`These are …` (plural **-s**)|"These are books."|
|104|L103|Near & Far|`this` vs `that`|"This is a bag. That is a board."|
|105|L104|Planet Gondax|`these` vs `those`|"These are pens. Those are desks."|
|106|L105|Four Pointers|mix this/that/these/those|(fix-it)|
|107|L106|Robot Roll-call|singular ↔ plural nouns (**-s/-es**)|box→boxes|
|108|L107|Count the Bots|number + plural noun|"two tablets"|
|109|L108|Sound Lab: oa/oi/oo|phonics + reading|(spell/read)|
|110|L109|Classroom Champion|**Unit 1 review** (mixed)|—|

### World 12 — Unit 2 · Family & Feelings  (L110–L119)
*Grammar arc: verb **to be** (am/is/are), personal pronouns, irregular plurals, demonstratives.*
Vocab: family (mom, dad, brother, sister, grandma, grandpa, baby) + feelings (happy, sad, tired, angry, scared, excited).

| Lvl | id | Quest / focus | Grammar target | Example |
|----|-----|----|----|----|
|111|L110|Gondax Castle|`I am` / `You are`|"I am Astro. You are my friend."|
|112|L111|The Royal Boat|`He/She/It is`|"She is my sister."|
|113|L112|The Whole Family|`We are` / `They are`|"They are my grandparents."|
|114|L113|Not True!|to be **negative** (isn't/aren't)|"He is not sad."|
|115|L114|The Giant Eagle|to be **questions**|"Are you happy?"|
|116|L115|How do you feel?|feelings + to be|"I am excited."|
|117|L116|Grandma's Chip|**irregular plurals**|man→men, child→children, foot→feet|
|118|L117|This is my family|demonstratives + to be|"This is my mom. These are my brothers."|
|119|L118|Sound Lab: air/ear/er|phonics + reading|—|
|120|L119|Family Champion|**Unit 2 review**|—|

### World 13 — Unit 3 · Activities  (L120–L129)
*Grammar arc: **can / can't** (ability), can-questions & short answers, action verbs.*
Vocab: action verbs (run, jump, swim, fly, climb, dance, sing, draw) + animals.

| Lvl | id | Quest / focus | Grammar target | Example |
|----|-----|----|----|----|
|121|L120|The Trampoline|`I can …`|"I can jump."|
|122|L121|Astro Gets a Sticker|`I can't …`|"I can't fly."|
|123|L122|Can you?|`Can you…?` → Yes I can / No I can't|"Can you swim? Yes, I can."|
|124|L123|Astro the Balloon|`He/She can …`|"She can dance."|
|125|L124|Action Station|action-verb vocab|—|
|126|L125|Animal Powers|animals + can|"A bird can fly."|
|127|L126|Can or Can't?|can vs can't (fix-it)|—|
|128|L127|New Spell|`What can you do?`|"What can you do? I can draw."|
|129|L128|Sound Lab: ur/or/ir|phonics + reading|—|
|130|L129|Activity Champion|**Unit 3 review**|—|

### World 14 — Unit 4 · My Things, Your Things  (L130–L139)
*Grammar arc: **have got / has got**, possessive adjectives & pronouns, possessive 's.*
Vocab: toys & hobbies (ball, kite, bike, doll, robot, puzzle, skateboard, guitar).

| Lvl | id | Quest / focus | Grammar target | Example |
|----|-----|----|----|----|
|131|L130|Astro Gets Wings|`I/You have got`|"I have got a kite."|
|132|L131|Chewing Gum|`He/She has got`|"She has got a doll."|
|133|L132|Nothing Left|have got **negative**|"He hasn't got a bike."|
|134|L133|Have you got?|have got **questions**|"Have you got a ball?"|
|135|L134|Whose is it?|possessive adjectives (my/your/his/her)|"This is her robot."|
|136|L135|Astro's Ball|possessive **'s**|"Astro's guitar is red."|
|137|L136|Mine & Yours|possessive pronouns (mine/yours/his/hers)|"The kite is mine."|
|138|L137|Toy Box|toys & hobbies vocab|—|
|139|L138|Sound Review|phonics review|—|
|140|L139|Things Champion|**Unit 4 review**|—|

### World 15 — Unit 5 · Food I Like  (L140–L149)
*Grammar arc: **present simple** like/don't like, 3rd-person likes/doesn't, object pronouns.*
Vocab: food (pizza, apple, rice, fish, cheese, cake, milk, soup).

| Lvl | id | Quest / focus | Grammar target | Example |
|----|-----|----|----|----|
|141|L140|A Yummy Mystery|`I like` / `I don't like`|"I like pizza. I don't like soup."|
|142|L141|Do you like it?|`Do you like…?` Yes/No|"Do you like fish? No, I don't."|
|143|L142|Mr Gluto Returns|`He/She likes` (**-s**)|"She likes cake."|
|144|L143|Nice Mr Gluto|`doesn't like`|"He doesn't like milk."|
|145|L144|Does he?|`Does he/she like…?`|"Does she like rice?"|
|146|L145|Me & Them|object pronouns (me/him/her/it/them)|"I like it. She likes them."|
|147|L146|Food Court|food vocab + like|—|
|148|L147|Ludo's Doubts|`like` vs `likes` (fix-it)|—|
|149|L148|Sound Lab: st/nd/mp|phonics + reading|—|
|150|L149|Food Champion|**Unit 5 review**|—|

### World 16 — Unit 6 · My Daily Routine  (L150–L159)
*Grammar arc: **present simple** for routines, telling time, frequency (light), questions.*
Vocab: routine verbs (get up, wash, eat, go, play, read, sleep, brush).

| Lvl | id | Quest / focus | Grammar target | Example |
|----|-----|----|----|----|
|151|L150|Barsu Wakes Up|routine verbs|"get up, wash, eat"|
|152|L151|My Day|present simple `I/you`|"I get up at seven."|
|153|L152|Students Are Not OK|present simple `he/she` (**-s**)|"She goes to school."|
|154|L153|Ludo Has a Plan|telling time (o'clock / half past)|"It's half past eight."|
|155|L154|Not Every Day|present simple negative|"He doesn't sleep at noon."|
|156|L155|When do you…?|present simple questions|"What time do you eat?"|
|157|L156|Always & Never|frequency (always/sometimes/never)|"I always brush my teeth."|
|158|L157|Slime Portal|routine + time (build)|"I read at night."|
|159|L158|Sound Lab: sk/lp/lt & cr/br|phonics + reading|—|
|160|L159|Routine Champion|**Unit 6 review**|—|

### World 17 — Unit 7 · Activities I Love  (L160–L169)
*Grammar arc: **present continuous** (am/is/are + -ing), -ing spelling, seasons & months.*
Vocab: outdoor actions (camping, running, swimming, riding, jumping, reading, cooking, painting) + seasons.

| Lvl | id | Quest / focus | Grammar target | Example |
|----|-----|----|----|----|
|161|L160|The Camping Trip|`I am + -ing`|"I am running."|
|162|L161|The Comet|`He/She is + -ing`|"She is swimming."|
|163|L162|Everyone's Busy|`They are + -ing`|"They are camping."|
|164|L163|Not Now|present continuous **negative**|"He isn't cooking."|
|165|L164|What are you doing?|present continuous **questions**|"What are you doing?"|
|166|L165|Sally's Lost Bag|**-ing spelling** (run→running, ride→riding)|—|
|167|L166|Seasons & Months|seasons/months vocab|"In summer I am swimming."|
|168|L167|Now vs Every Day|simple vs continuous (light contrast)|—|
|169|L168|Sound Lab: tr/dr/gr|phonics + reading|—|
|170|L169|Action Champion|**Unit 7 review**|—|

### World 18 — Unit 8 · How Much, How Many  (L170–L179)
*Grammar arc: countable/uncountable, quantifiers (some/any/a lot of), how much/how many, would like, prepositions of place, capitalisation.*
Vocab: food & containers (bread, water, apples, eggs, rice, juice, bananas, sugar).

| Lvl | id | Quest / focus | Grammar target | Example |
|----|-----|----|----|----|
|171|L170|The Plopster|countable vs uncountable (**sort**)|apples ↔ rice|
|172|L171|A, An, Some|`a/an` vs `some`|"an egg / some rice"|
|173|L172|Count Them|`How many…?` (countable)|"How many eggs?"|
|174|L173|Plopster Asleep|`How much…?` (uncountable)|"How much water?"|
|175|L174|Some or Any?|`some` / `any`|"I don't have any sugar."|
|176|L175|Wake the Plopster|`I would like…` (**'d like**)|"I would like some juice."|
|177|L176|Where's the Egg?|prepositions of place (in/on/under/next to)|"The egg is under the box."|
|178|L177|Big Letters|**capitalisation** (I, names, sentence start)|"I live in Tel Aviv."|
|179|L178|Sound Lab: bl/fl/gl & cl/pl|phonics + reading|—|
|180|L179|Quantity Champion|**Unit 8 review**|—|

### World 19 — Unit 9 · Let's Compare  (L180–L189)
*Grammar arc: **comparative adjectives** (-er / more … than), irregular comparatives, countries & nationalities.*
Vocab: adjectives (big, small, fast, slow, tall, short, long, strong) + animals/countries.

| Lvl | id | Quest / focus | Grammar target | Example |
|----|-----|----|----|----|
|181|L180|The Empty Zoo|adjectives review|big/small/fast/slow|
|182|L181|The Fireflies|comparative **-er**|"bigger, smaller"|
|183|L182|Bigger Than|`… -er than …`|"A lion is bigger than a cat."|
|184|L183|Spelling Rules|comparative spelling (big→bigger, happy→happier)|—|
|185|L184|Better or Worse|**irregular** (good→better, bad→worse)|—|
|186|L185|More Beautiful|`more + long adjective`|"more beautiful"|
|187|L186|Slime Maker|countries & nationalities|"She is from Spain."|
|188|L187|The Talking Bubbles|compare things (build)|—|
|189|L188|Sound Lab: tw/sm/sp|phonics + reading|—|
|190|L189|Compare Champion|**Unit 9 review**|—|

### World 20 — Unit 10 · Places & Past  (L190–L199)
*Grammar arc: **was / were** (past of be), there was/were, prepositions & directions, places & transport. Finale.*
Vocab: places & transport (school, park, shop, bus, car, train, bike, plane).

| Lvl | id | Quest / focus | Grammar target | Example |
|----|-----|----|----|----|
|191|L190|Don't Look at the Slime|places & transport vocab|—|
|192|L191|The Shrinking Machine|`was / were`|"I was at school. They were at the park."|
|193|L192|Not There|was/were **negative**|"He wasn't on the bus."|
|194|L193|The Slime Empire|was/were **questions**|"Were you at home?"|
|195|L194|There Was a Slime|`There was / There were`|"There were three cars."|
|196|L195|Giving Directions|prepositions & directions|"Turn left. It's next to the shop."|
|197|L196|Yesterday|past time markers (yesterday, last…)|"Yesterday I was at the park."|
|198|L197|Novus Comes to Help|places + was/were (build)|—|
|199|L198|Sound Lab: nch/scr/shr/str|phonics + reading|—|
|200|L199|Grand Grammar Finale|**mastery of Units 1–10**|—|

> **Phonics levels (every world's Lvl-9)** map straight to `level.md`'s "Letter Sounds"
> lessons. They stay word-level (they lean on `spell_it`, `listen_pick_word`,
> `look_pick_word`) and need no new mechanic — they reuse the vocab-game engine with the
> unit's blend words. Include ≥6 spellable words (`^[a-z]+$`, length 3–7) so `spell_it`
> always has material.

---

## 4. Data model — the new `grammar` block

Add **one optional field** to each level: `grammar`. It feeds the new mini-games. It is
authored in `build_assets.py` alongside the level's words. Vocab levels 0–99 omit it.

```jsonc
"grammar": {
  "target": "This is / These are",          // short human label; spoken when the level starts

  // pick_word_gap  — fill the blank
  "gap": [
    { "text": "___ is a cat.",    "options": ["This", "These", "Those"], "correct": 0, "emoji": "🐱" },
    { "text": "___ are books.",   "options": ["This", "These"],          "correct": 1, "emoji": "📚" }
  ],

  // transform  — make the right form
  "transform": [
    { "prompt": "one cat →",  "base": "cat", "options": ["cats", "cates", "cat"], "correct": 0 },
    { "prompt": "one box →",  "base": "box", "options": ["boxs", "boxes", "box"], "correct": 1 }
  ],

  // fix_sentence  — pick the correct sentence (right vs wrong)
  "fix": [
    { "right": "These are apples.", "wrong": "These is apples.", "emoji": "🍎" },
    { "right": "This is a pen.",    "wrong": "This is a apple.", "emoji": "🖊️" }
  ],

  // sort_rule  — drop each token in the right rule-box
  "sort": {
    "binA": "one",  "binB": "many",
    "tokens": [
      { "t": "a cat",     "cat": "A", "emoji": "🐱" },
      { "t": "three dogs","cat": "B", "emoji": "🐶" },
      { "t": "a book",    "cat": "A", "emoji": "📕" },
      { "t": "two pens",  "cat": "B", "emoji": "🖊️" },
      { "t": "an apple",  "cat": "A", "emoji": "🍎" }
    ]
  }
}
```

**Authoring rules (so games never break):**
- `gap`: ≥ 3 entries; each 2–4 `options`; `correct` in range. Keep `text` ≤ ~6 words.
- `transform`: ≥ 3 entries; 3 options each; exactly one `correct`.
- `fix`: ≥ 3 entries; `right`/`wrong` differ by exactly the target structure.
- `sort`: ≥ 5 tokens, at least 2 of each `cat`; short, speakable `t`.
- **`sentences`** (existing field) becomes the level's set of *grammar exemplars* for
  Build a Sentence — write 4–6 correct target sentences (e.g. "These are my books.",
  "He is not sad.", "The lion is bigger than the cat."). Questions ("Can you swim?") and
  contractions ("don't", "isn't") are fine — Build a Sentence strips/keeps final
  `. ? !` and treats each space-separated token (incl. `don't`) as one tile.

If a grammar array is missing/short for a chosen game, the game must **fall back**
gracefully (see each spec) — never render empty.

---

## 5. Per-level game recipe (`level.gameTypes`)

Today every level shuffles **all** `DATA.gameTypes`. Grammar levels instead declare an
explicit 10-game line-up mixing **grammar** and **vocab reinforcement**. Recommended
default recipe for a grammar level (order is shuffled by the engine anyway):

| # | game type | kind | source data |
|---|-----------|------|-------------|
| 1 | `listen_pick_picture` | vocab warm-up | `items` |
| 2 | `look_pick_word` | vocab | `items` |
| 3 | `pick_word_gap` ⭐ | **grammar** | `grammar.gap` |
| 4 | `build_sentence` ⭐ | **grammar** | `sentences` |
| 5 | `sort_rule` ⭐ | **grammar** | `grammar.sort` |
| 6 | `transform` ⭐ | **grammar** | `grammar.transform` |
| 7 | `fix_sentence` ⭐ | **grammar** | `grammar.fix` |
| 8 | `true_false` | grammar-ish | `items` (keep) |
| 9 | `spell_it` | vocab | `items` |
| 10 | `say_it` | speaking | `items` |

**Phonics levels (Lvl-9 of each world)** swap the grammar-heavy slots for word games:
`listen_pick_picture, look_pick_word, look_pick_sound, match_pairs, listen_pick_word,
spell_it, say_it, build_sentence, sort_it, true_false`.

**Review levels (Lvl-10)** use a broad mix drawing on all four grammar games so the
child re-meets every structure from the unit.

> Keep exactly **10** entries so `gamesPerSession` stays 10 and the progress dots/score
> are unchanged. Repeats are allowed if a world lacks data for a game.

---

## 6. New mini-games — full specs (`app.js`)

Add each to the `GAMES` map. Follow the existing style (plain DOM via `api.el`, reuse
`singleChoice`, always `api.registerSolver` so the e2e sweep can auto-play). Each game
**must** call `api.finish()` on success and `api.addMistake()` + `api.wrong()` on a
wrong tap — that is the entire scoring contract.

### 6.1 `pick_word_gap` — "Choose the Word" (gap-fill)
The workhorse grammar game. Show a sentence with a blank + a picture, tap the word that
fills it.

- **Data:** one entry from `api.level.grammar.gap` (via `api.pick`). Fallback if absent:
  derive a trivial gap from a sentence (blank the first word) — but every grammar level
  ships `gap`, so this is just a guard.
- **UI:** instruction "🧩 Tap the missing word"; prompt = the sentence with the blank
  rendered as a chip (and the emoji flashcard if present); options via `singleChoice`
  (`instant: true`, one option per `options[]`, `correct` from data). `onSelect` speaks
  the tapped word; on correct, `api.speak(full sentence with blank filled)` then finish.
- **Solver:** provided free by `singleChoice`.
- **Audio needs:** each full-filled sentence + each option word (see §8).

### 6.2 `transform` — "Change the Word" (morphology)
Teach plural -s/-es, 3rd-person -s, -ing, comparative -er, irregulars.

- **Data:** one entry from `grammar.transform`. Fallback: none needed (guard → `finish`).
- **UI:** instruction "🔧 Make the right word"; prompt shows `prompt` (e.g. "one cat →")
  with the base word spoken; `singleChoice` over `options`, `correct` from data,
  `renderOption` = the word text, `instant: true`. On correct, speak the target word.
- **Solver:** from `singleChoice`.

### 6.3 `fix_sentence` — "Fix It" (correct vs incorrect)
Two sentence cards, one grammatical and one not; tap the correct one.

- **Data:** one entry from `grammar.fix` (`right`, `wrong`, optional `emoji`).
- **UI:** instruction "🕵️ Which one is right?"; optional emoji flashcard prompt;
  `singleChoice` with `twoUp: true`, two options `[{s:right},{s:wrong}]` **shuffled**
  (compute `correct` = index of the right one after shuffle), `renderOption` = a card
  showing the sentence text + a 🔊 that speaks it, `onSelect` speaks the tapped sentence.
  On correct, speak `right` and finish; wrong tap → `addMistake`/`wrong`, leave both up.
- **Solver:** register one that clicks the card whose text === `right`
  (`api.registerSolver`) and a wrong solver that clicks the other (for the WRONG-run test).
- **Enhancement (optional):** a "tap the wrong word" variant — out of scope for v1.

### 6.4 `sort_rule` — "Sort by Rule" (generalised Sort It)
Same tactile mechanic as the existing `sort_it`, but the two bins are **grammar
categories** with explicit labels, and tokens are grammar phrases, not other levels'
vocab.

- **Preferred:** generalise the existing `sort_it`: **if `api.level.grammar.sort` exists,
  build bins from `binA`/`binB` and tokens from `grammar.sort.tokens`** (each token:
  render `api.picNode`-style card from `emoji` + `t`, category `cat`); **else** keep the
  current behavior (this level's items vs a random other level's). This keeps levels
  0–99 identical and needs no new registered type — but you **should still register a
  distinct `sort_rule` id** in `GAME_TYPES` (its own instruction) and route it to the
  same renderer so the recipe can request it explicitly. Simplest: `sort_rule` and
  `sort_it` share one function that branches on the data.
- **Token rendering:** tokens carry an `emoji` but no `slug`/`image`; render a small card
  with the emoji (reuse the emoji-fallback path `api.picNode` already has) so no new SVGs
  are required.
- **Solver / wrong-solver:** the existing `sort_it` solver logic (click the correct bin
  for the current token; wrong-solver clicks the other bin) works unchanged.

> **Do NOT** point `sort_rule` at other levels' items for grammar bins — the label must
> be a rule ("one" / "many"), and the category is per-token, so it must come from
> `grammar.sort`.

---

## 7. Engine change (the only edit to game flow)

In `startSession` (app.js ~line 459), choose the line-up from the level when present:

```js
var typeIds = (level.gameTypes && level.gameTypes.length)
  ? level.gameTypes.slice()
  : DATA.gameTypes.map(function (g) { return g.id; });
var order = shuffle(typeIds);
this.session = { level: level, pool: level.items.slice(), sentences: level.sentences,
                 order: order, index: 0, mistakes: 0, results: [] };
```

`renderGame`/`completeGame` already look a game up by id from `DATA.gameTypes` (`.name`,
`.instruction`), so **add the 4 new types to `DATA.gameTypes`** (via `GAME_TYPES` in
build_assets) and they resolve automatically. No other flow change.

To keep levels 0–99 at exactly their original 10 games once the master list grows to 14,
**give every level an explicit `gameTypes`** in build_assets (vocab levels → the original
10 ids; grammar levels → the recipe). The engine falls back to "all" only if a level has
none.

---

## 8. Build-script changes

### 8.1 `build_assets.py`
1. **Add the 10 grammar worlds.** Either extend `WORLDS` with a richer per-level tuple,
   or (cleaner) add a parallel `GRAMMAR_WORLDS` list whose entries also carry `grammar`,
   `sentences`, and `gameTypes`, and append their levels after the vocab levels so global
   `index` continues 100…199. Keep `slugify`, image generation, palette cycling as-is.
2. **Emit the new per-level fields:** `grammar` (object) and `gameTypes` (list of ids).
   Also set `gameTypes` = the original 10 for the existing vocab levels.
3. **Register the 4 new game types** in `GAME_TYPES` (id + name + instruction), e.g.:
   ```py
   {"id": "pick_word_gap", "name": "Choose the Word", "instruction": "Tap the missing word!"},
   {"id": "transform",     "name": "Change the Word", "instruction": "Make the right word!"},
   {"id": "fix_sentence",  "name": "Fix It",          "instruction": "Tap the sentence that is right!"},
   {"id": "sort_rule",     "name": "Sort by Rule",    "instruction": "Put each one in the right box!"},
   ```
4. **Generate any new images** for grammar `items` emojis automatically (existing loop
   already writes one SVG per unique slug). Grammar `sort`/`gap` tokens use `emoji` only
   (no SVG needed — emoji fallback).
5. Bump `meta.totalLevels` (it's already `len(levels_out)` → becomes 200 automatically).

### 8.2 `build_audio.py`
Extend `collect_texts()` to also record the new spoken strings, or the game will fall
back to Web Speech (acceptable, but ship real clips for consistency). Add, per level:

```py
g = lv.get("grammar")
if g:
    add(g.get("target", ""))
    for e in g.get("gap", []):
        add(e["text"].replace("___", e["options"][e["correct"]]))   # the filled sentence
        for o in e["options"]: add(o)
    for e in g.get("transform", []):
        add(e["prompt"]); add(e["base"])
        for o in e["options"]: add(o)
    for e in g.get("fix", []):
        add(e["right"]); add(e["wrong"])
    s = g.get("sort")
    if s:
        add(s["binA"]); add(s["binB"])
        for t in s["tokens"]: add(t["t"])
```

New `gameTypes` instructions are already picked up by the existing
`for gt in data["gameTypes"]: add(gt["instruction"])` loop. Then run
`python3 build_assets.py && python3 build_audio.py` (audio on macOS).

---

## 9. Testing (`test_e2e.py`)

The sweep already: for **every** level, plays "one of each game type present that
session", checks a WRONG run scores < 95 and keeps the next level locked, and a CORRECT
run scores 100 and unlocks the next — sweeping to the last level. It will extend to 200
automatically **provided each new game registers solvers**:

- `pick_word_gap`, `transform`, `fix_sentence` → correct + wrong solvers (the first two
  get them from `singleChoice`; `fix_sentence` registers both explicitly, §6.3).
- `sort_rule` → reuse `sort_it`'s solver/wrong-solver.

Add light assertions (optional): on one grammar level (e.g. L100), assert a
`pick_word_gap` prompt contains a blank and that tapping the correct option finishes; on
a `fix_sentence`, assert the wrong card does not finish. Keep the fast automation mode so
200 levels × ~10 games still run in a few minutes.

**Acceptance checklist**
- [ ] `build_assets.py` emits 200 levels; ids L000–L199; `worldIndex` 0–15; every level
      has `gameTypes` (10 ids) and grammar levels have a valid `grammar` block.
- [ ] `data.js`/`content.json` regenerate; `meta.totalLevels == 200`.
- [ ] 4 new games render, are solvable, score correctly, and award stars.
- [ ] Home map shows 16 worlds; L100 unlocks after L99 scores ≥ 95; chain runs to L199.
- [ ] `build_audio.py` produces clips for all new text (or Web-Speech fallback verified).
- [ ] `python test_e2e.py` passes start-to-finish across all 200 levels.
- [ ] Levels 0–99 are byte-for-byte unchanged in behavior (same 10 games, same scores).

---

## 10. Worked example — one complete grammar level (L100 = "Level 101")

This is exactly what `build_assets.py` should emit for the first grammar level. Copy the
shape for all 100.

```jsonc
{
  "id": "L100",
  "index": 100,
  "world": "Digital Classroom",
  "worldSubtitle": "This & These — Magic Academy Unit 1",
  "worldIndex": 6,
  "name": "The Alien Princess",
  "category": "L100",
  "color": "#BFE2FF",
  "items": [
    { "word": "pen",    "emoji": "🖊️", "slug": "pen",    "image": "images/pen.svg",    "color": "#BFE2FF" },
    { "word": "book",   "emoji": "📕", "slug": "book",   "image": "images/book.svg",   "color": "#BFE2FF" },
    { "word": "bag",    "emoji": "🎒", "slug": "bag",    "image": "images/bag.svg",    "color": "#BFE2FF" },
    { "word": "desk",   "emoji": "🪑", "slug": "desk",   "image": "images/desk.svg",   "color": "#BFE2FF" },
    { "word": "ruler",  "emoji": "📏", "slug": "ruler",  "image": "images/ruler.svg",  "color": "#BFE2FF" },
    { "word": "tablet", "emoji": "📱", "slug": "tablet", "image": "images/tablet.svg", "color": "#BFE2FF" },
    { "word": "apple",  "emoji": "🍎", "slug": "apple",  "image": "images/apple.svg",  "color": "#BFE2FF" }
  ],
  "sentences": [
    "This is a pen.",
    "This is a book.",
    "This is an apple.",
    "Look at my bag!",
    "This is my desk."
  ],
  "gameTypes": [
    "listen_pick_picture", "look_pick_word", "pick_word_gap", "build_sentence",
    "sort_rule", "transform", "fix_sentence", "true_false", "spell_it", "say_it"
  ],
  "grammar": {
    "target": "This is a / an",
    "gap": [
      { "text": "This is ___ pen.",   "options": ["a", "an"],  "correct": 0, "emoji": "🖊️" },
      { "text": "This is ___ apple.", "options": ["a", "an"],  "correct": 1, "emoji": "🍎" },
      { "text": "___ is a book.",     "options": ["This", "These"], "correct": 0, "emoji": "📕" }
    ],
    "transform": [
      { "prompt": "one book →",  "base": "book",  "options": ["books", "bookes", "book"],   "correct": 0 },
      { "prompt": "one bag →",   "base": "bag",   "options": ["bages", "bags", "bag"],      "correct": 1 },
      { "prompt": "one ruler →", "base": "ruler", "options": ["ruler", "rulers", "rulor"],  "correct": 1 }
    ],
    "fix": [
      { "right": "This is a pen.",   "wrong": "This is an pen.",   "emoji": "🖊️" },
      { "right": "This is an apple.","wrong": "This is a apple.",  "emoji": "🍎" },
      { "right": "This is my bag.",  "wrong": "This is my bags.",  "emoji": "🎒" }
    ],
    "sort": {
      "binA": "a",
      "binB": "an",
      "tokens": [
        { "t": "pen",    "cat": "A", "emoji": "🖊️" },
        { "t": "apple",  "cat": "B", "emoji": "🍎" },
        { "t": "book",   "cat": "A", "emoji": "📕" },
        { "t": "orange", "cat": "B", "emoji": "🍊" },
        { "t": "desk",   "cat": "A", "emoji": "🪑" }
      ]
    }
  }
}
```

---

## 11. Notes, risks & choices

- **Why extend, not fork.** The engine, scoring, persistence, ranks, and map are already
  data-driven and level-count-agnostic. Extending keeps the child's whole history (stars,
  unlocks) intact and gives the grammar half the exact same tactile feel — the strongest
  guarantee it "feels like the first 100".
- **Grammar is taught through doing.** `build_sentence` (order), `pick_word_gap`
  (choose), `transform` (form), `fix_sentence` (notice error), `sort_rule` (categorise)
  cover the four ways beginners internalise a structure. Every world hits all four.
- **Reading/phonics** stay in the word-game engine (Lvl-9 of each world) — faithful to
  `level.md`'s "Letter Sounds" lessons without new mechanics.
- **Difficulty & fairness.** Keep grammar options short and *minimally* different so a
  wrong tap teaches the contrast (`is`/`are`, `a`/`an`, `like`/`likes`). Never require
  reading beyond the unit's vocab.
- **Optional polish (not required for v1):** a distinct visual banner/color band for the
  "Magic Academy" story worlds; a "tap the wrong word" variant of `fix_sentence`; a
  mid-world mini-boss review. None affect the acceptance criteria.
```
