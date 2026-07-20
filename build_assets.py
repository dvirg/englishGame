#!/usr/bin/env python3
"""
build_assets.py  —  Magic Academy: English Quest
=================================================
Single source of truth for ALL game content (now ~100 levels).

    python3 build_assets.py

Outputs (next to this file):
    content.json      Pretty structured data file (the canonical curriculum).
    data.js           `window.GAME_DATA = {...}` — loaded by the browser.
    images/<slug>.svg One small, colorful picture per vocabulary word.

Curriculum
----------
Content is organized into "worlds" that mirror the real Novakid ladder
(Pre-K -> Juniors -> Starters -> Movers -> Flyers -> Explorers). Each world
holds several **levels**; a level is one playable topic (a 10-game session).
Levels are numbered globally and are unlocked in order: the next level opens
once the player scores >= 95 on the current one (handled in app.js).

The Starters world follows the Level 2 units from the reference screenshots
(Digital Classroom, Family & Feelings, Activities, My things, Food, Daily
routine, Activities I love, Food quantity, Let's compare, Places & past).

Media
-----
* Pictures: real, small SVG files in ./images (one per word) that render the
  matching emoji on a colored card, referenced by each item's `image` field.
  The app falls back to a live emoji if a file is missing, so pictures never
  break. Colors cycle per level for variety.
* Audio: generated live in the browser by the Web Speech API with an en-US
  (American) voice — see app.js. No audio files are shipped.
"""

import json
import os
import random
import re

HERE = os.path.dirname(os.path.abspath(__file__))
IMAGES_DIR = os.path.join(HERE, "images")

# Pleasant pastel card backgrounds, cycled per level.
PALETTE = [
    "#FFE7A8", "#DCC9FF", "#FFD0DE", "#C6F0CE", "#BFE2FF", "#FFE0C4",
    "#CDEBFF", "#CBF3E1", "#FFE0D5", "#E9DDFF", "#FDE2B3", "#D8F0FF",
    "#FFD6C9", "#D6F5C9", "#E6D3FF", "#C9F0EC",
]


def slugify(word):
    return re.sub(r"[^a-z0-9]+", "-", word.lower()).strip("-")


def make_asset_slug(word, emoji, context, used_slugs):
    base = slugify(word)
    if not base:
        base = "item"

    if base not in used_slugs:
        used_slugs[base] = (emoji, context)
        return base

    if used_slugs[base][0] == emoji:
        return base

    candidate = slugify("%s-%s" % (word, context)) or "%s-%s" % (base, "item")
    if candidate not in used_slugs:
        used_slugs[candidate] = (emoji, context)
        return candidate

    if used_slugs[candidate][0] == emoji:
        return candidate

    n = 2
    while True:
        alt = "%s-%d" % (candidate, n)
        if alt not in used_slugs:
            used_slugs[alt] = (emoji, context)
            return alt
        if used_slugs[alt][0] == emoji:
            return alt
        n += 1


def plural_for(word):
    w = word.lower().rstrip()
    if w.endswith(("s", "x", "z", "ch", "sh")):
        return w + "es"
    if w.endswith("y") and len(w) > 1 and w[-2] not in "aeiou":
        return w[:-1] + "ies"
    return w + "s"


def make_sentences(items, base=None):
    base = base or []
    words = [it[0] for it in items[:6]]
    if not words:
        words = ["word"]
    sentences = []
    for w in words[:4]:
        sentences.append("This is a %s." % w)
    if len(words) > 1:
        sentences.append("These are %s." % plural_for(words[1]))
    if len(words) > 2:
        sentences.append("I like the %s." % words[2])
    if len(base):
        sentences.extend(base)
    return sentences[:6]


def make_grammar(theme, items):
    def pick(i):
        return items[i][0] if i < len(items) else (items[0][0] if items else "word")

    word1 = pick(0)
    word2 = pick(1)
    word3 = pick(2)
    word4 = pick(3)
    word5 = pick(4)
    word6 = pick(5)
    if theme == "this-an":
        target = "This is a / an"
        gap = [
            {"text": "This is ___ %s." % word1, "options": ["a", "an"], "correct": 0, "emoji": items[0][1] if items else "🖊️"},
            {"text": "This is ___ %s." % word2, "options": ["a", "an"], "correct": 1, "emoji": items[1][1] if len(items) > 1 else "📚"},
            {"text": "___ is a %s." % word3, "options": ["This", "These"], "correct": 0, "emoji": items[2][1] if len(items) > 2 else "🎒"},
        ]
        transform = [
            {"prompt": "one %s →" % word1, "base": word1, "options": [plural_for(word1), word1 + "es", word1], "correct": 0},
            {"prompt": "one %s →" % word2, "base": word2, "options": [word2 + "s", plural_for(word2), word2], "correct": 1},
            {"prompt": "one %s →" % word3, "base": word3, "options": [plural_for(word3), word3 + "s", word3], "correct": 0},
        ]
        fix = [
            {"right": "This is a %s." % word1, "wrong": "This is an %s." % word1, "emoji": items[0][1] if items else "🖊️"},
            {"right": "This is an %s." % word2, "wrong": "This is a %s." % word2, "emoji": items[1][1] if len(items) > 1 else "🍎"},
            {"right": "This is my %s." % word3, "wrong": "This is my %ss." % word3, "emoji": items[2][1] if len(items) > 2 else "🎒"},
        ]
        sort = {"binA": "a", "binB": "an", "tokens": [
            {"t": word1, "cat": "A", "emoji": items[0][1] if items else "🖊️"},
            {"t": word2, "cat": "B", "emoji": items[1][1] if len(items) > 1 else "🍎"},
            {"t": word3, "cat": "A", "emoji": items[2][1] if len(items) > 2 else "📕"},
            {"t": word4, "cat": "B", "emoji": items[3][1] if len(items) > 3 else "🧸"},
            {"t": word5, "cat": "A", "emoji": items[4][1] if len(items) > 4 else "🪑"},
        ]}
    elif theme == "to-be":
        target = "To be"
        gap = [
            {"text": "I ___ happy.", "options": ["am", "is", "are"], "correct": 0, "emoji": "😀"},
            {"text": "She ___ my sister.", "options": ["is", "am", "are"], "correct": 0, "emoji": "👧"},
            {"text": "We ___ friends.", "options": ["are", "is", "am"], "correct": 0, "emoji": "🤝"},
        ]
        transform = [
            {"prompt": "I am →", "base": "am", "options": ["are", "is", "am"], "correct": 2},
            {"prompt": "she is →", "base": "is", "options": ["are", "is", "am"], "correct": 1},
            {"prompt": "you are →", "base": "are", "options": ["are", "is", "am"], "correct": 0},
        ]
        fix = [
            {"right": "I am happy.", "wrong": "I is happy.", "emoji": "😀"},
            {"right": "She is my sister.", "wrong": "She are my sister.", "emoji": "👧"},
            {"right": "We are friends.", "wrong": "We am friends.", "emoji": "🤝"},
        ]
        sort = {"binA": "am/is", "binB": "are", "tokens": [
            {"t": "I am", "cat": "A", "emoji": "😀"},
            {"t": "she is", "cat": "A", "emoji": "👧"},
            {"t": "you are", "cat": "B", "emoji": "🧒"},
            {"t": "we are", "cat": "B", "emoji": "👨‍👩‍👧"},
            {"t": "it is", "cat": "A", "emoji": "🐱"},
        ]}
    elif theme == "can":
        target = "Can / can't"
        gap = [
            {"text": "I ___ jump.", "options": ["can", "can't"], "correct": 0, "emoji": "🤸"},
            {"text": "She ___ fly.", "options": ["can", "can't"], "correct": 1, "emoji": "🦅"},
            {"text": "___ you swim?", "options": ["Can", "Do"], "correct": 0, "emoji": "🏊"},
        ]
        transform = [
            {"prompt": "can →", "base": "can", "options": ["can't", "can", "cans"], "correct": 0},
            {"prompt": "can't →", "base": "can't", "options": ["can't", "can", "cant"], "correct": 0},
            {"prompt": "can swim →", "base": "swim", "options": ["swims", "swim", "swiming"], "correct": 1},
        ]
        fix = [
            {"right": "I can jump.", "wrong": "I can jumps.", "emoji": "🤸"},
            {"right": "She can't fly.", "wrong": "She can not fly.", "emoji": "🦅"},
            {"right": "Can you swim?", "wrong": "Can you swims?", "emoji": "🏊"},
        ]
        sort = {"binA": "can", "binB": "can't", "tokens": [
            {"t": "I can run", "cat": "A", "emoji": "🏃"},
            {"t": "I can't fly", "cat": "B", "emoji": "🦅"},
            {"t": "She can dance", "cat": "A", "emoji": "💃"},
            {"t": "He can't swim", "cat": "B", "emoji": "🏊"},
            {"t": "We can sing", "cat": "A", "emoji": "🎤"},
        ]}
    elif theme == "have-got":
        target = "Have got / has got"
        gap = [
            {"text": "I ___ a kite.", "options": ["have got", "has got"], "correct": 0, "emoji": "🪁"},
            {"text": "She ___ a doll.", "options": ["has got", "have got"], "correct": 0, "emoji": "🧸"},
            {"text": "___ you got a ball?", "options": ["Have", "Has"], "correct": 0, "emoji": "⚽"},
        ]
        transform = [
            {"prompt": "I have got →", "base": "have got", "options": ["has got", "have get", "have got"], "correct": 2},
            {"prompt": "she has got →", "base": "has got", "options": ["have got", "has got", "has get"], "correct": 1},
            {"prompt": "have got →", "base": "have got", "options": ["has got", "have got", "got"], "correct": 1},
        ]
        fix = [
            {"right": "I have got a kite.", "wrong": "I has got a kite.", "emoji": "🪁"},
            {"right": "She has got a doll.", "wrong": "She have got a doll.", "emoji": "🧸"},
            {"right": "Have you got a ball?", "wrong": "Has you got a ball?", "emoji": "⚽"},
        ]
        sort = {"binA": "have got", "binB": "has got", "tokens": [
            {"t": "I have got a bike", "cat": "A", "emoji": "🚲"},
            {"t": "She has got a doll", "cat": "B", "emoji": "🧸"},
            {"t": "We have got a robot", "cat": "A", "emoji": "🤖"},
            {"t": "He has got a puzzle", "cat": "B", "emoji": "🧩"},
            {"t": "You have got a guitar", "cat": "A", "emoji": "🎸"},
        ]}
    elif theme == "like":
        target = "Like / likes"
        gap = [
            {"text": "I ___ pizza.", "options": ["like", "likes"], "correct": 0, "emoji": "🍕"},
            {"text": "She ___ cake.", "options": ["likes", "like"], "correct": 0, "emoji": "🍰"},
            {"text": "Do you ___ fish?", "options": ["like", "likes"], "correct": 0, "emoji": "🐟"},
        ]
        transform = [
            {"prompt": "I like →", "base": "like", "options": ["likes", "like", "liking"], "correct": 0},
            {"prompt": "he likes →", "base": "likes", "options": ["like", "likes", "likess"], "correct": 1},
            {"prompt": "do like →", "base": "like", "options": ["likes", "like", "liked"], "correct": 1},
        ]
        fix = [
            {"right": "She likes cake.", "wrong": "She like cake.", "emoji": "🍰"},
            {"right": "I like pizza.", "wrong": "I likes pizza.", "emoji": "🍕"},
            {"right": "Do you like fish?", "wrong": "Do you likes fish?", "emoji": "🐟"},
        ]
        sort = {"binA": "like", "binB": "likes", "tokens": [
            {"t": "I like milk", "cat": "A", "emoji": "🥛"},
            {"t": "She likes cake", "cat": "B", "emoji": "🍰"},
            {"t": "We like apples", "cat": "A", "emoji": "🍎"},
            {"t": "He likes soup", "cat": "B", "emoji": "🍲"},
            {"t": "They like rice", "cat": "A", "emoji": "🍚"},
        ]}
    elif theme == "routine":
        target = "Present simple routine"
        gap = [
            {"text": "I ___ up at seven.", "options": ["get", "gets"], "correct": 0, "emoji": "⏰"},
            {"text": "She ___ to school.", "options": ["goes", "go"], "correct": 0, "emoji": "🏫"},
            {"text": "We ___ dinner at six.", "options": ["eat", "eats"], "correct": 0, "emoji": "🍽️"},
        ]
        transform = [
            {"prompt": "go →", "base": "go", "options": ["goes", "go", "going"], "correct": 0},
            {"prompt": "eat →", "base": "eat", "options": ["eats", "eat", "eated"], "correct": 0},
            {"prompt": "brush →", "base": "brush", "options": ["brushes", "brush", "brushing"], "correct": 0},
        ]
        fix = [
            {"right": "She goes to school.", "wrong": "She go to school.", "emoji": "🏫"},
            {"right": "I get up at seven.", "wrong": "I gets up at seven.", "emoji": "⏰"},
            {"right": "We eat dinner at six.", "wrong": "We eats dinner at six.", "emoji": "🍽️"},
        ]
        sort = {"binA": "I/you", "binB": "he/she", "tokens": [
            {"t": "I get up", "cat": "A", "emoji": "⏰"},
            {"t": "She reads", "cat": "B", "emoji": "📖"},
            {"t": "You play", "cat": "A", "emoji": "🎮"},
            {"t": "He sleeps", "cat": "B", "emoji": "😴"},
            {"t": "We wash", "cat": "A", "emoji": "🧼"},
        ]}
    elif theme == "present-cont":
        target = "Present continuous"
        gap = [
            {"text": "I ___ running.", "options": ["am", "is", "are"], "correct": 0, "emoji": "🏃"},
            {"text": "She ___ swimming.", "options": ["is", "am", "are"], "correct": 0, "emoji": "🏊"},
            {"text": "They ___ camping.", "options": ["are", "is", "am"], "correct": 0, "emoji": "⛺"},
        ]
        transform = [
            {"prompt": "run →", "base": "run", "options": ["running", "runned", "runs"], "correct": 0},
            {"prompt": "ride →", "base": "ride", "options": ["riding", "ride", "rides"], "correct": 0},
            {"prompt": "cook →", "base": "cook", "options": ["cooking", "cooks", "cook"], "correct": 0},
        ]
        fix = [
            {"right": "She is swimming.", "wrong": "She are swimming.", "emoji": "🏊"},
            {"right": "They are camping.", "wrong": "They is camping.", "emoji": "⛺"},
            {"right": "I am running.", "wrong": "I is running.", "emoji": "🏃"},
        ]
        sort = {"binA": "am/is", "binB": "are", "tokens": [
            {"t": "I am running", "cat": "A", "emoji": "🏃"},
            {"t": "She is reading", "cat": "A", "emoji": "📖"},
            {"t": "They are jumping", "cat": "B", "emoji": "🤸"},
            {"t": "We are painting", "cat": "B", "emoji": "🎨"},
            {"t": "He is cooking", "cat": "A", "emoji": "🍳"},
        ]}
    elif theme == "quantity":
        target = "How much / how many"
        gap = [
            {"text": "___ apples?", "options": ["How many", "How much"], "correct": 0, "emoji": "🍎"},
            {"text": "___ water?", "options": ["How much", "How many"], "correct": 0, "emoji": "💧"},
            {"text": "I would like ___ juice.", "options": ["some", "a"], "correct": 0, "emoji": "🧃"},
        ]
        transform = [
            {"prompt": "apple →", "base": "apple", "options": ["apples", "apple", "app"], "correct": 0},
            {"prompt": "water →", "base": "water", "options": ["water", "waters", "wata"], "correct": 0},
            {"prompt": "egg →", "base": "egg", "options": ["eggs", "egg", "eg"], "correct": 0},
        ]
        fix = [
            {"right": "How many apples?", "wrong": "How much apples?", "emoji": "🍎"},
            {"right": "How much water?", "wrong": "How many water?", "emoji": "💧"},
            {"right": "I would like some juice.", "wrong": "I would like a juice.", "emoji": "🧃"},
        ]
        sort = {"binA": "how many", "binB": "how much", "tokens": [
            {"t": "How many apples", "cat": "A", "emoji": "🍎"},
            {"t": "How much water", "cat": "B", "emoji": "💧"},
            {"t": "How many eggs", "cat": "A", "emoji": "🥚"},
            {"t": "How much rice", "cat": "B", "emoji": "🍚"},
            {"t": "How many bananas", "cat": "A", "emoji": "🍌"},
        ]}
    elif theme == "comparative":
        target = "Comparatives"
        gap = [
            {"text": "A lion is ___ than a cat.", "options": ["bigger", "big"], "correct": 0, "emoji": "🦁"},
            {"text": "A snail is ___ than a rocket.", "options": ["slower", "slow"], "correct": 0, "emoji": "🐌"},
            {"text": "A giraffe is ___ than a dog.", "options": ["taller", "tall"], "correct": 0, "emoji": "🦒"},
        ]
        transform = [
            {"prompt": "big →", "base": "big", "options": ["bigger", "biger", "biggest"], "correct": 0},
            {"prompt": "happy →", "base": "happy", "options": ["happier", "happyer", "happiest"], "correct": 0},
            {"prompt": "good →", "base": "good", "options": ["better", "gooder", "best"], "correct": 0},
        ]
        fix = [
            {"right": "A lion is bigger than a cat.", "wrong": "A lion is big than a cat.", "emoji": "🦁"},
            {"right": "A snail is slower than a rocket.", "wrong": "A snail is slow than a rocket.", "emoji": "🐌"},
            {"right": "A giraffe is taller than a dog.", "wrong": "A giraffe is tall than a dog.", "emoji": "🦒"},
        ]
        sort = {"binA": "-er", "binB": "more", "tokens": [
            {"t": "bigger", "cat": "A", "emoji": "🦁"},
            {"t": "more beautiful", "cat": "B", "emoji": "🌸"},
            {"t": "smaller", "cat": "A", "emoji": "🐜"},
            {"t": "more interesting", "cat": "B", "emoji": "🔍"},
            {"t": "faster", "cat": "A", "emoji": "🚀"},
        ]}
    else:
        target = "Review"
        gap = [
            {"text": "This is ___ %s." % word1, "options": ["a", "an"], "correct": 0, "emoji": items[0][1] if items else "🖊️"},
            {"text": "I ___ happy.", "options": ["am", "is"], "correct": 0, "emoji": "😀"},
            {"text": "She ___ cake.", "options": ["likes", "like"], "correct": 0, "emoji": "🍰"},
        ]
        transform = [
            {"prompt": "one %s →" % word1, "base": word1, "options": [plural_for(word1), word1, word1 + "s"], "correct": 0},
            {"prompt": "run →", "base": "run", "options": ["running", "runs", "run"], "correct": 0},
            {"prompt": "big →", "base": "big", "options": ["bigger", "big", "biggest"], "correct": 0},
        ]
        fix = [
            {"right": "This is a %s." % word1, "wrong": "This is an %s." % word1, "emoji": items[0][1] if items else "🖊️"},
            {"right": "She likes cake.", "wrong": "She like cake.", "emoji": "🍰"},
            {"right": "I am happy.", "wrong": "I is happy.", "emoji": "😀"},
        ]
        sort = {"binA": "one", "binB": "many", "tokens": [
            {"t": "a %s" % word1, "cat": "A", "emoji": items[0][1] if items else "🖊️"},
            {"t": "three %ss" % word2, "cat": "B", "emoji": items[1][1] if len(items) > 1 else "🧸"},
            {"t": "an %s" % word3, "cat": "A", "emoji": items[2][1] if len(items) > 2 else "📕"},
            {"t": "two %ss" % word4, "cat": "B", "emoji": items[3][1] if len(items) > 3 else "🎒"},
            {"t": "a %s" % word5, "cat": "A", "emoji": items[4][1] if len(items) > 4 else "🪑"},
        ]}
    return {"target": target, "gap": gap, "transform": transform, "fix": fix, "sort": sort}


# ---------------------------------------------------------------------------
# WORLDS -> LEVELS -> (word, emoji)
# Each level: (topic name, [(word, emoji), ...]). >= 5 words so every game
# (which needs 4 options / 4 pairs) always has enough material.
# ---------------------------------------------------------------------------
WORLDS = [
    ("Pre-K Planet", "First tiny words", [
        ("Colors", [("red", "🔴"), ("blue", "🔵"), ("green", "🟢"), ("yellow", "🟡"), ("orange", "🟠"), ("purple", "🟣"), ("pink", "🌸"), ("black", "⚫")]),
        ("Numbers 1-5", [("one", "1️⃣"), ("two", "2️⃣"), ("three", "3️⃣"), ("four", "4️⃣"), ("five", "5️⃣")]),
        ("Numbers 6-10", [("six", "6️⃣"), ("seven", "7️⃣"), ("eight", "8️⃣"), ("nine", "9️⃣"), ("ten", "🔟")]),
        ("Shapes", [("star", "⭐"), ("heart", "❤️"), ("circle", "⚪"), ("square", "🟦"), ("diamond", "💎"), ("moon", "🌙")]),
        ("Pets", [("cat", "🐱"), ("dog", "🐶"), ("fish", "🐟"), ("rabbit", "🐰"), ("bird", "🐦"), ("mouse", "🐭")]),
        ("Farm Animals", [("cow", "🐮"), ("pig", "🐷"), ("horse", "🐴"), ("sheep", "🐑"), ("duck", "🦆"), ("hen", "🐔")]),
        ("My Body", [("hand", "✋"), ("eye", "👁️"), ("nose", "👃"), ("ear", "👂"), ("mouth", "👄"), ("foot", "🦶")]),
        ("Fruit", [("apple", "🍎"), ("banana", "🍌"), ("orange", "🍊"), ("grapes", "🍇"), ("strawberry", "🍓"), ("melon", "🍉")]),
        ("Toys", [("ball", "⚽"), ("teddy", "🧸"), ("doll", "🪆"), ("car", "🚗"), ("kite", "🪁"), ("blocks", "🧱")]),
        ("Family", [("mom", "👩"), ("dad", "👨"), ("baby", "👶"), ("brother", "👦"), ("sister", "👧"), ("grandma", "👵"), ("grandpa", "👴")]),
        ("Faces", [("smile", "😊"), ("cry", "😭"), ("laugh", "😂"), ("wink", "😉"), ("yawn", "🥱"), ("angry", "😠")]),
        ("Snacks", [("cookie", "🍪"), ("candy", "🍬"), ("popcorn", "🍿"), ("lollipop", "🍭"), ("chocolate", "🍫"), ("cupcake", "🧁")]),
    ]),

    ("Juniors Jungle", "Lots of first words", [
        ("Wild Animals", [("lion", "🦁"), ("tiger", "🐯"), ("elephant", "🐘"), ("monkey", "🐵"), ("bear", "🐻"), ("zebra", "🦓")]),
        ("Sea Animals", [("whale", "🐳"), ("dolphin", "🐬"), ("octopus", "🐙"), ("crab", "🦀"), ("shark", "🦈"), ("fish", "🐟")]),
        ("Birds", [("owl", "🦉"), ("duck", "🦆"), ("chicken", "🐔"), ("penguin", "🐧"), ("eagle", "🦅"), ("parrot", "🦜")]),
        ("Bugs", [("bee", "🐝"), ("ant", "🐜"), ("butterfly", "🦋"), ("spider", "🕷️"), ("ladybug", "🐞"), ("snail", "🐌")]),
        ("Vegetables", [("carrot", "🥕"), ("tomato", "🍅"), ("potato", "🥔"), ("corn", "🌽"), ("broccoli", "🥦"), ("pepper", "🫑")]),
        ("Food", [("bread", "🍞"), ("cheese", "🧀"), ("egg", "🥚"), ("rice", "🍚"), ("meat", "🍖"), ("soup", "🍲")]),
        ("Drinks", [("water", "💧"), ("milk", "🥛"), ("juice", "🧃"), ("tea", "🍵"), ("coffee", "☕"), ("soda", "🥤")]),
        ("Sweets", [("cake", "🍰"), ("ice cream", "🍦"), ("cookie", "🍪"), ("candy", "🍬"), ("chocolate", "🍫"), ("donut", "🍩")]),
        ("Clothes", [("shirt", "👕"), ("pants", "👖"), ("dress", "👗"), ("shoes", "👟"), ("hat", "🎩"), ("socks", "🧦")]),
        ("Weather", [("sun", "☀️"), ("rain", "🌧️"), ("snow", "❄️"), ("cloud", "☁️"), ("wind", "🌬️"), ("rainbow", "🌈")]),
        ("Home", [("house", "🏠"), ("door", "🚪"), ("window", "🪟"), ("bed", "🛏️"), ("chair", "🪑"), ("clock", "🕐")]),
        ("Kitchen", [("cup", "☕"), ("plate", "🍽️"), ("fork", "🍴"), ("spoon", "🥄"), ("knife", "🔪"), ("pot", "🍲")]),
        ("Garden", [("flower", "🌸"), ("tree", "🌳"), ("grass", "🌿"), ("leaf", "🍃"), ("seed", "🌱"), ("bug", "🐛")]),
        ("Nature", [("mountain", "⛰️"), ("river", "🏞️"), ("beach", "🏖️"), ("forest", "🌲"), ("sky", "🌌"), ("fire", "🔥")]),
        ("Colors 2", [("pink", "🌸"), ("brown", "🤎"), ("white", "⚪"), ("black", "⚫"), ("gray", "🔘"), ("blue", "🔵")]),
        ("In the Sky", [("sun", "☀️"), ("moon", "🌙"), ("star", "⭐"), ("cloud", "☁️"), ("rainbow", "🌈"), ("kite", "🪁")]),
        ("Water Fun", [("fish", "🐟"), ("boat", "⛵"), ("duck", "🦆"), ("wave", "🌊"), ("shell", "🐚"), ("crab", "🦀")]),
    ]),

    ("Starters Station", "Tzofia's Magic Academy", [
        ("Classroom", [("pen", "🖊️"), ("pencil", "✏️"), ("book", "📚"), ("bag", "🎒"), ("ruler", "📏"), ("crayon", "🖍️")]),
        ("At School", [("school", "🏫"), ("teacher", "🧑‍🏫"), ("student", "🧑‍🎓"), ("desk", "🪑"), ("board", "🖼️"), ("clock", "🕐")]),
        ("Feelings", [("happy", "😀"), ("sad", "😢"), ("angry", "😠"), ("sleepy", "😪"), ("scared", "😨"), ("surprised", "😮")]),
        ("Action Words", [("run", "🏃"), ("jump", "🤸"), ("walk", "🚶"), ("swim", "🏊"), ("climb", "🧗"), ("dance", "💃")]),
        ("Zoo Animals", [("giraffe", "🦒"), ("kangaroo", "🦘"), ("panda", "🐼"), ("koala", "🐨"), ("hippo", "🦛"), ("camel", "🐫")]),
        ("Toys & Hobbies", [("bike", "🚲"), ("guitar", "🎸"), ("puzzle", "🧩"), ("game", "🎮"), ("kite", "🪁"), ("ball", "⚽")]),
        ("Yummy Food", [("pizza", "🍕"), ("sandwich", "🥪"), ("salad", "🥗"), ("pasta", "🍝"), ("burger", "🍔"), ("fries", "🍟")]),
        ("Daily Routine", [("wake", "⏰"), ("eat", "🍽️"), ("wash", "🧼"), ("sleep", "😴"), ("read", "📖"), ("play", "🎮")]),
        ("Time of Day", [("morning", "🌅"), ("afternoon", "🌤️"), ("evening", "🌆"), ("night", "🌙"), ("clock", "🕐"), ("watch", "⌚")]),
        ("Seasons", [("spring", "🌷"), ("summer", "☀️"), ("autumn", "🍂"), ("winter", "❄️"), ("rain", "🌧️"), ("snow", "⛄")]),
        ("Camping Trip", [("tent", "⛺"), ("fire", "🔥"), ("backpack", "🎒"), ("map", "🗺️"), ("torch", "🔦"), ("boots", "🥾")]),
        ("Picnic", [("apple", "🍎"), ("juice", "🧃"), ("cake", "🍰"), ("sandwich", "🥪"), ("banana", "🍌"), ("water", "💧")]),
        ("Opposites", [("big", "🐘"), ("small", "🐜"), ("fast", "🚀"), ("slow", "🐌"), ("hot", "🔥"), ("cold", "🧊")]),
        ("Transport", [("car", "🚗"), ("bus", "🚌"), ("train", "🚆"), ("plane", "✈️"), ("boat", "⛵"), ("bike", "🚲")]),
        ("Places in Town", [("shop", "🏪"), ("school", "🏫"), ("park", "🏞️"), ("hospital", "🏥"), ("house", "🏠"), ("castle", "🏰")]),
        ("Days & Time", [("clock", "🕐"), ("alarm", "⏰"), ("calendar", "📅"), ("watch", "⌚"), ("day", "☀️"), ("night", "🌙")]),
        ("My Week", [("school", "🏫"), ("home", "🏠"), ("park", "🏞️"), ("shop", "🏪"), ("play", "🎮"), ("sleep", "😴")]),
        ("Feelings 2", [("excited", "🤩"), ("tired", "😫"), ("hungry", "😋"), ("thirsty", "🥤"), ("love", "❤️"), ("bored", "😑")]),
        ("Weather Today", [("sunny", "☀️"), ("rainy", "🌧️"), ("snowy", "❄️"), ("cloudy", "☁️"), ("windy", "🌬️"), ("stormy", "⛈️")]),
        ("In the City", [("car", "🚗"), ("bus", "🚌"), ("shop", "🏪"), ("park", "🏞️"), ("road", "🛣️"), ("light", "🚦")]),
    ]),

    ("Movers Mountain", "Bigger words & ideas", [
        ("Jobs", [("doctor", "🧑‍⚕️"), ("teacher", "🧑‍🏫"), ("chef", "👨‍🍳"), ("police", "👮"), ("farmer", "🧑‍🌾"), ("pilot", "🧑‍✈️")]),
        ("Sports", [("soccer", "⚽"), ("basketball", "🏀"), ("tennis", "🎾"), ("baseball", "⚾"), ("swimming", "🏊"), ("running", "🏃")]),
        ("Music", [("guitar", "🎸"), ("piano", "🎹"), ("drums", "🥁"), ("violin", "🎻"), ("trumpet", "🎺"), ("microphone", "🎤")]),
        ("Space", [("sun", "☀️"), ("moon", "🌙"), ("star", "⭐"), ("planet", "🪐"), ("rocket", "🚀"), ("astronaut", "🧑‍🚀")]),
        ("Big Vehicles", [("helicopter", "🚁"), ("ship", "🚢"), ("truck", "🚚"), ("taxi", "🚕"), ("motorbike", "🏍️"), ("tractor", "🚜")]),
        ("Wild Weather", [("storm", "⛈️"), ("fog", "🌫️"), ("lightning", "⚡"), ("tornado", "🌪️"), ("sunny", "☀️"), ("windy", "🌬️")]),
        ("More Feelings", [("excited", "🤩"), ("bored", "😑"), ("shy", "😳"), ("proud", "😌"), ("nervous", "😰"), ("silly", "🤪")]),
        ("House Rooms", [("kitchen", "🍳"), ("bedroom", "🛏️"), ("bathroom", "🛁"), ("garden", "🌳"), ("garage", "🚗"), ("sofa", "🛋️")]),
        ("Shopping", [("money", "💵"), ("coin", "🪙"), ("shop", "🏪"), ("bag", "🛍️"), ("card", "💳"), ("gift", "🎁")]),
        ("At the Doctor", [("doctor", "🧑‍⚕️"), ("medicine", "💊"), ("hospital", "🏥"), ("sick", "🤒"), ("bandage", "🩹"), ("tooth", "🦷")]),
        ("Party Time", [("cake", "🎂"), ("balloon", "🎈"), ("gift", "🎁"), ("candle", "🕯️"), ("music", "🎵"), ("party", "🥳")]),
        ("At the Ocean", [("wave", "🌊"), ("boat", "⛵"), ("shell", "🐚"), ("sand", "🏖️"), ("island", "🏝️"), ("fish", "🐟")]),
        ("More Fruit", [("pineapple", "🍍"), ("mango", "🥭"), ("cherry", "🍒"), ("peach", "🍑"), ("lemon", "🍋"), ("kiwi", "🥝")]),
        ("More Veggies", [("onion", "🧅"), ("garlic", "🧄"), ("mushroom", "🍄"), ("cucumber", "🥒"), ("eggplant", "🍆"), ("lettuce", "🥬")]),
        ("Forest Animals", [("fox", "🦊"), ("wolf", "🐺"), ("deer", "🦌"), ("raccoon", "🦝"), ("hedgehog", "🦔"), ("bat", "🦇")]),
        ("More Farm", [("goat", "🐐"), ("rooster", "🐓"), ("llama", "🦙"), ("turkey", "🦃"), ("rabbit", "🐰"), ("mouse", "🐭")]),
        ("Around the World", [("map", "🗺️"), ("globe", "🌍"), ("flag", "🚩"), ("plane", "✈️"), ("luggage", "🧳"), ("camera", "📷")]),
        ("Feeling Faces", [("smile", "😊"), ("frown", "☹️"), ("cry", "😭"), ("laugh", "😂"), ("shocked", "😲"), ("sleepy", "😴")]),
        ("Garden Friends", [("bee", "🐝"), ("sunflower", "🌻"), ("butterfly", "🦋"), ("tree", "🌳"), ("bird", "🐦"), ("sun", "☀️")]),
    ]),

    ("Flyers Forest", "Clever explorer words", [
        ("Reptiles", [("snake", "🐍"), ("turtle", "🐢"), ("lizard", "🦎"), ("crocodile", "🐊"), ("frog", "🐸"), ("dinosaur", "🦕")]),
        ("Big Nature", [("volcano", "🌋"), ("desert", "🏜️"), ("forest", "🌲"), ("waterfall", "🏞️"), ("cave", "🕳️"), ("ocean", "🌊")]),
        ("The Sky", [("lightning", "⚡"), ("tornado", "🌪️"), ("snowflake", "❄️"), ("sunrise", "🌅"), ("sunset", "🌇"), ("stars", "🌌")]),
        ("Technology", [("phone", "📱"), ("computer", "💻"), ("tv", "📺"), ("camera", "📷"), ("robot", "🤖"), ("game", "🎮")]),
        ("School Subjects", [("math", "➕"), ("science", "🔬"), ("art", "🎨"), ("music", "🎵"), ("reading", "📖"), ("sport", "⚽")]),
        ("Winter Clothes", [("coat", "🧥"), ("scarf", "🧣"), ("gloves", "🧤"), ("boots", "🥾"), ("cap", "🧢"), ("tie", "👔")]),
        ("More Jobs", [("artist", "🧑‍🎨"), ("singer", "🧑‍🎤"), ("scientist", "🧑‍🔬"), ("astronaut", "🧑‍🚀"), ("firefighter", "🧑‍🚒"), ("builder", "👷")]),
        ("World Food", [("sushi", "🍣"), ("taco", "🌮"), ("noodles", "🍜"), ("pancake", "🥞"), ("popcorn", "🍿"), ("pretzel", "🥨")]),
        ("Cool Drinks", [("smoothie", "🥤"), ("lemonade", "🍋"), ("milkshake", "🥛"), ("tea", "🍵"), ("water", "💧"), ("juice", "🧃")]),
        ("Halloween", [("pumpkin", "🎃"), ("ghost", "👻"), ("bat", "🦇"), ("spider", "🕷️"), ("witch", "🧙"), ("skeleton", "💀")]),
        ("Christmas", [("tree", "🎄"), ("gift", "🎁"), ("santa", "🎅"), ("snowman", "⛄"), ("bell", "🔔"), ("star", "⭐")]),
        ("At the Beach", [("umbrella", "⛱️"), ("sandcastle", "🏰"), ("shell", "🐚"), ("wave", "🌊"), ("sun", "☀️"), ("crab", "🦀")]),
        ("City Vehicles", [("police car", "🚓"), ("ambulance", "🚑"), ("fire truck", "🚒"), ("subway", "🚇"), ("scooter", "🛴"), ("skateboard", "🛹")]),
        ("Tropical Fruit", [("coconut", "🥥"), ("avocado", "🥑"), ("blueberry", "🫐"), ("pear", "🍐"), ("cherry", "🍒"), ("kiwi", "🥝")]),
        ("Royal Jobs", [("king", "🤴"), ("queen", "👸"), ("guard", "💂"), ("prince", "🧑‍🦰"), ("knight", "🛡️"), ("crown", "👑")]),
        ("Camping Gear", [("compass", "🧭"), ("tent", "⛺"), ("fire", "🔥"), ("map", "🗺️"), ("backpack", "🎒"), ("flashlight", "🔦")]),
        ("Desserts 2", [("pie", "🥧"), ("honey", "🍯"), ("pudding", "🍮"), ("cupcake", "🧁"), ("lollipop", "🍭"), ("waffle", "🧇")]),
    ]),

    ("Explorers Galaxy", "Master challenges", [
        ("Tools", [("hammer", "🔨"), ("wrench", "🔧"), ("screwdriver", "🪛"), ("saw", "🪚"), ("pin", "📌"), ("ruler", "📏")]),
        ("Music 2", [("headphones", "🎧"), ("note", "🎵"), ("saxophone", "🎷"), ("bell", "🔔"), ("speaker", "🔊"), ("piano", "🎹")]),
        ("Sports 2", [("golf", "⛳"), ("boxing", "🥊"), ("skiing", "🎿"), ("skating", "⛸️"), ("cycling", "🚴"), ("surfing", "🏄")]),
        ("Big Zoo", [("rhino", "🦏"), ("peacock", "🦚"), ("gorilla", "🦍"), ("flamingo", "🦩"), ("sloth", "🦥"), ("otter", "🦦")]),
        ("Baby Animals", [("puppy", "🐶"), ("kitten", "🐱"), ("chick", "🐤"), ("piglet", "🐷"), ("bunny", "🐰"), ("duckling", "🐥")]),
        ("Ocean Deep", [("jellyfish", "🪼"), ("lobster", "🦞"), ("seal", "🦭"), ("shrimp", "🦐"), ("turtle", "🐢"), ("squid", "🦑")]),
        ("More Bugs", [("grasshopper", "🦗"), ("mosquito", "🦟"), ("beetle", "🪲"), ("fly", "🪰"), ("worm", "🪱"), ("cricket", "🦗")]),
        ("Dinosaurs", [("dinosaur", "🦕"), ("t-rex", "🦖"), ("dragon", "🐉"), ("lizard", "🦎"), ("egg", "🥚"), ("bone", "🦴")]),
        ("Fantasy", [("fairy", "🧚"), ("wizard", "🧙"), ("unicorn", "🦄"), ("dragon", "🐉"), ("crown", "👑"), ("magic", "✨")]),
        ("Buildings", [("castle", "🏰"), ("tower", "🗼"), ("church", "⛪"), ("factory", "🏭"), ("stadium", "🏟️"), ("house", "🏠")]),
        ("Deep Space", [("earth", "🌍"), ("saturn", "🪐"), ("comet", "☄️"), ("galaxy", "🌌"), ("telescope", "🔭"), ("ufo", "🛸")]),
        ("Meals", [("breakfast", "🍳"), ("lunch", "🍱"), ("dinner", "🍽️"), ("snack", "🍿"), ("salad", "🥗"), ("fruit", "🍎")]),
        ("Body 2", [("arm", "💪"), ("leg", "🦵"), ("hair", "💇"), ("teeth", "🦷"), ("tongue", "👅"), ("finger", "👆")]),
        ("Champions", [("star", "⭐"), ("trophy", "🏆"), ("medal", "🏅"), ("balloon", "🎈"), ("party", "🥳"), ("gift", "🎁")]),
        ("Grand Finale", [("trophy", "🏆"), ("medal", "🏅"), ("crown", "👑"), ("star", "🌟"), ("fireworks", "🎆"), ("rocket", "🚀")]),
    ]),
]

GRAMMAR_WORLDS = [
    ("Digital Classroom", "This & These — Magic Academy Unit 1", [
        ("The Alien Princess", [("pen", "🖊️"), ("book", "📚"), ("bag", "🎒"), ("desk", "🪑"), ("ruler", "📏"), ("apple", "🍎")], "this-an"),
        ("A or An?", [("apple", "🍎"), ("egg", "🥚"), ("orange", "🍊"), ("umbrella", "☔"), ("ant", "🐜"), ("ice cream", "🍦")], "this-an"),
        ("Through the Portal", [("book", "📚"), ("pencil", "✏️"), ("desk", "🪑"), ("bag", "🎒"), ("chair", "🪑"), ("tablet", "📱")], "this-an"),
        ("Near & Far", [("bag", "🎒"), ("board", "🖼️"), ("desk", "🪑"), ("chair", "🪑"), ("pen", "🖊️"), ("ruler", "📏")], "this-an"),
        ("Planet Gondax", [("pen", "🖊️"), ("pencil", "✏️"), ("book", "📚"), ("desk", "🪑"), ("chair", "🪑"), ("tablet", "📱")], "this-an"),
        ("Four Pointers", [("bag", "🎒"), ("board", "🖼️"), ("desk", "🪑"), ("chair", "🪑"), ("table", "🪑"), ("pencil", "✏️")], "this-an"),
        ("Robot Roll-call", [("box", "📦"), ("bus", "🚌"), ("dress", "👗"), ("glass", "🫙"), ("watch", "⌚"), ("brush", "🪥")], "this-an"),
        ("Count the Bots", [("two", "2️⃣"), ("three", "3️⃣"), ("four", "4️⃣"), ("five", "5️⃣"), ("six", "6️⃣"), ("seven", "7️⃣")], "this-an"),
        ("Sound Lab", [("boat", "⛵"), ("coin", "🪙"), ("food", "🍽️"), ("school", "🏫"), ("book", "📚"), ("room", "🏠")], "this-an"),
        ("Classroom Champion", [("pen", "🖊️"), ("book", "📚"), ("bag", "🎒"), ("desk", "🪑"), ("ruler", "📏"), ("tablet", "📱")], "this-an"),
    ]),
    ("Family & Feelings", "To be — Magic Academy Unit 2", [
        ("Gondax Castle", [("mom", "👩"), ("dad", "👨"), ("brother", "👦"), ("sister", "👧"), ("baby", "👶"), ("friend", "🤝")], "to-be"),
        ("The Royal Boat", [("mom", "👩"), ("dad", "👨"), ("grandma", "👵"), ("grandpa", "👴"), ("sister", "👧"), ("brother", "👦")], "to-be"),
        ("The Whole Family", [("family", "👨‍👩‍👧"), ("grandma", "👵"), ("grandpa", "👴"), ("baby", "👶"), ("sister", "👧"), ("brother", "👦")], "to-be"),
        ("Not True!", [("happy", "😀"), ("sad", "😢"), ("angry", "😠"), ("scared", "😨"), ("tired", "😫"), ("excited", "🤩")], "to-be"),
        ("The Giant Eagle", [("happy", "😀"), ("sad", "😢"), ("angry", "😠"), ("scared", "😨"), ("tired", "😫"), ("excited", "🤩")], "to-be"),
        ("How do you feel?", [("happy", "😀"), ("sad", "😢"), ("angry", "😠"), ("scared", "😨"), ("tired", "😫"), ("excited", "🤩")], "to-be"),
        ("Grandma's Chip", [("man", "🧔"), ("woman", "👩"), ("child", "🧒"), ("foot", "🦶"), ("tooth", "🦷"), ("mouse", "🐭")], "to-be"),
        ("This is my family", [("mom", "👩"), ("dad", "👨"), ("brother", "👦"), ("sister", "👧"), ("baby", "👶"), ("grandma", "👵")], "to-be"),
        ("Sound Lab", [("bear", "🐻"), ("chair", "🪑"), ("clear", "🔦"), ("near", "🏠"), ("year", "📅"), ("hear", "👂")], "to-be"),
        ("Family Champion", [("mom", "👩"), ("dad", "👨"), ("brother", "👦"), ("sister", "👧"), ("baby", "👶"), ("happy", "😀")], "to-be"),
    ]),
    ("Activities", "Can / can't — Magic Academy Unit 3", [
        ("The Trampoline", [("run", "🏃"), ("jump", "🤸"), ("swim", "🏊"), ("dance", "💃"), ("sing", "🎤"), ("draw", "🎨")], "can"),
        ("Astro Gets a Sticker", [("run", "🏃"), ("jump", "🤸"), ("swim", "🏊"), ("fly", "🦅"), ("climb", "🧗"), ("dance", "💃")], "can"),
        ("Can you?", [("run", "🏃"), ("jump", "🤸"), ("swim", "🏊"), ("dance", "💃"), ("sing", "🎤"), ("draw", "🎨")], "can"),
        ("Astro the Balloon", [("dance", "💃"), ("sing", "🎤"), ("draw", "🎨"), ("climb", "🧗"), ("jump", "🤸"), ("run", "🏃")], "can"),
        ("Action Station", [("run", "🏃"), ("jump", "🤸"), ("swim", "🏊"), ("climb", "🧗"), ("dance", "💃"), ("draw", "🎨")], "can"),
        ("Animal Powers", [("bird", "🐦"), ("fish", "🐟"), ("monkey", "🐵"), ("horse", "🐴"), ("duck", "🦆"), ("owl", "🦉")], "can"),
        ("Can or Can't?", [("jump", "🤸"), ("fly", "🦅"), ("swim", "🏊"), ("climb", "🧗"), ("dance", "💃"), ("sing", "🎤")], "can"),
        ("New Spell", [("draw", "🎨"), ("sing", "🎤"), ("dance", "💃"), ("swim", "🏊"), ("run", "🏃"), ("jump", "🤸")], "can"),
        ("Sound Lab", [("bird", "🐦"), ("girl", "👧"), ("shirt", "👕"), ("turn", "🔄"), ("work", "🛠️"), ("word", "🗣️")], "can"),
        ("Activity Champion", [("run", "🏃"), ("jump", "🤸"), ("swim", "🏊"), ("dance", "💃"), ("sing", "🎤"), ("draw", "🎨")], "can"),
    ]),
    ("My Things, Your Things", "Have got — Magic Academy Unit 4", [
        ("Astro Gets Wings", [("kite", "🪁"), ("ball", "⚽"), ("bike", "🚲"), ("doll", "🧸"), ("robot", "🤖"), ("puzzle", "🧩")], "have-got"),
        ("Chewing Gum", [("kite", "🪁"), ("ball", "⚽"), ("bike", "🚲"), ("doll", "🧸"), ("robot", "🤖"), ("guitar", "🎸")], "have-got"),
        ("Nothing Left", [("kite", "🪁"), ("ball", "⚽"), ("bike", "🚲"), ("doll", "🧸"), ("robot", "🤖"), ("puzzle", "🧩")], "have-got"),
        ("Have you got?", [("ball", "⚽"), ("bike", "🚲"), ("doll", "🧸"), ("kite", "🪁"), ("robot", "🤖"), ("guitar", "🎸")], "have-got"),
        ("Whose is it?", [("robot", "🤖"), ("ball", "⚽"), ("bike", "🚲"), ("doll", "🧸"), ("kite", "🪁"), ("puzzle", "🧩")], "have-got"),
        ("Astro's Ball", [("ball", "⚽"), ("bike", "🚲"), ("doll", "🧸"), ("robot", "🤖"), ("guitar", "🎸"), ("puzzle", "🧩")], "have-got"),
        ("Mine & Yours", [("kite", "🪁"), ("ball", "⚽"), ("bike", "🚲"), ("doll", "🧸"), ("robot", "🤖"), ("puzzle", "🧩")], "have-got"),
        ("Toy Box", [("ball", "⚽"), ("bike", "🚲"), ("doll", "🧸"), ("kite", "🪁"), ("robot", "🤖"), ("guitar", "🎸")], "have-got"),
        ("Sound Review", [("ball", "⚽"), ("bike", "🚲"), ("doll", "🧸"), ("kite", "🪁"), ("robot", "🤖"), ("puzzle", "🧩")], "have-got"),
        ("Things Champion", [("ball", "⚽"), ("bike", "🚲"), ("doll", "🧸"), ("kite", "🪁"), ("robot", "🤖"), ("guitar", "🎸")], "have-got"),
    ]),
    ("Food I Like", "Like / likes — Magic Academy Unit 5", [
        ("A Yummy Mystery", [("pizza", "🍕"), ("apple", "🍎"), ("rice", "🍚"), ("fish", "🐟"), ("cheese", "🧀"), ("cake", "🍰")], "like"),
        ("Do you like it?", [("pizza", "🍕"), ("apple", "🍎"), ("rice", "🍚"), ("fish", "🐟"), ("cheese", "🧀"), ("cake", "🍰")], "like"),
        ("Mr Gluto Returns", [("pizza", "🍕"), ("apple", "🍎"), ("rice", "🍚"), ("fish", "🐟"), ("cheese", "🧀"), ("cake", "🍰")], "like"),
        ("Nice Mr Gluto", [("pizza", "🍕"), ("apple", "🍎"), ("rice", "🍚"), ("fish", "🐟"), ("cheese", "🧀"), ("cake", "🍰")], "like"),
        ("Does he?", [("pizza", "🍕"), ("apple", "🍎"), ("rice", "🍚"), ("fish", "🐟"), ("cheese", "🧀"), ("cake", "🍰")], "like"),
        ("Me & Them", [("pizza", "🍕"), ("apple", "🍎"), ("rice", "🍚"), ("fish", "🐟"), ("cheese", "🧀"), ("cake", "🍰")], "like"),
        ("Food Court", [("pizza", "🍕"), ("apple", "🍎"), ("rice", "🍚"), ("fish", "🐟"), ("cheese", "🧀"), ("cake", "🍰")], "like"),
        ("Ludo's Doubts", [("pizza", "🍕"), ("apple", "🍎"), ("rice", "🍚"), ("fish", "🐟"), ("cheese", "🧀"), ("cake", "🍰")], "like"),
        ("Sound Lab", [("pizza", "🍕"), ("apple", "🍎"), ("rice", "🍚"), ("fish", "🐟"), ("cheese", "🧀"), ("cake", "🍰")], "like"),
        ("Food Champion", [("pizza", "🍕"), ("apple", "🍎"), ("rice", "🍚"), ("fish", "🐟"), ("cheese", "🧀"), ("cake", "🍰")], "like"),
    ]),
    ("My Daily Routine", "Present simple routine — Magic Academy Unit 6", [
        ("Barsu Wakes Up", [("get up", "⏰"), ("wash", "🧼"), ("eat", "🍽️"), ("go", "🚶"), ("play", "🎮"), ("sleep", "😴")], "routine"),
        ("My Day", [("get up", "⏰"), ("wash", "🧼"), ("eat", "🍽️"), ("go", "🚶"), ("play", "🎮"), ("sleep", "😴")], "routine"),
        ("Students Are Not OK", [("get up", "⏰"), ("wash", "🧼"), ("eat", "🍽️"), ("go", "🚶"), ("play", "🎮"), ("sleep", "😴")], "routine"),
        ("Ludo Has a Plan", [("get up", "⏰"), ("wash", "🧼"), ("eat", "🍽️"), ("go", "🚶"), ("play", "🎮"), ("sleep", "😴")], "routine"),
        ("Not Every Day", [("get up", "⏰"), ("wash", "🧼"), ("eat", "🍽️"), ("go", "🚶"), ("play", "🎮"), ("sleep", "😴")], "routine"),
        ("When do you…?", [("get up", "⏰"), ("wash", "🧼"), ("eat", "🍽️"), ("go", "🚶"), ("play", "🎮"), ("sleep", "😴")], "routine"),
        ("Always & Never", [("get up", "⏰"), ("wash", "🧼"), ("eat", "🍽️"), ("go", "🚶"), ("play", "🎮"), ("sleep", "😴")], "routine"),
        ("Slime Portal", [("get up", "⏰"), ("wash", "🧼"), ("eat", "🍽️"), ("go", "🚶"), ("play", "🎮"), ("sleep", "😴")], "routine"),
        ("Sound Lab", [("get up", "⏰"), ("wash", "🧼"), ("eat", "🍽️"), ("go", "🚶"), ("play", "🎮"), ("sleep", "😴")], "routine"),
        ("Routine Champion", [("get up", "⏰"), ("wash", "🧼"), ("eat", "🍽️"), ("go", "🚶"), ("play", "🎮"), ("sleep", "😴")], "routine"),
    ]),
    ("Activities I Love", "Present continuous — Magic Academy Unit 7", [
        ("The Camping Trip", [("camping", "⛺"), ("running", "🏃"), ("swimming", "🏊"), ("riding", "🚲"), ("jumping", "🤸"), ("reading", "📖")], "present-cont"),
        ("The Comet", [("camping", "⛺"), ("running", "🏃"), ("swimming", "🏊"), ("riding", "🚲"), ("jumping", "🤸"), ("reading", "📖")], "present-cont"),
        ("Everyone's Busy", [("camping", "⛺"), ("running", "🏃"), ("swimming", "🏊"), ("riding", "🚲"), ("jumping", "🤸"), ("reading", "📖")], "present-cont"),
        ("Not Now", [("camping", "⛺"), ("running", "🏃"), ("swimming", "🏊"), ("riding", "🚲"), ("jumping", "🤸"), ("reading", "📖")], "present-cont"),
        ("What are you doing?", [("camping", "⛺"), ("running", "🏃"), ("swimming", "🏊"), ("riding", "🚲"), ("jumping", "🤸"), ("reading", "📖")], "present-cont"),
        ("Sally's Lost Bag", [("running", "🏃"), ("riding", "🚲"), ("swimming", "🏊"), ("jumping", "🤸"), ("cooking", "🍳"), ("painting", "🎨")], "present-cont"),
        ("Seasons & Months", [("summer", "☀️"), ("winter", "❄️"), ("spring", "🌷"), ("autumn", "🍂"), ("month", "📅"), ("holiday", "🎉")], "present-cont"),
        ("Now vs Every Day", [("running", "🏃"), ("swimming", "🏊"), ("reading", "📖"), ("cooking", "🍳"), ("painting", "🎨"), ("sleeping", "😴")], "present-cont"),
        ("Sound Lab", [("running", "🏃"), ("swimming", "🏊"), ("painting", "🎨"), ("cooking", "🍳"), ("riding", "🚲"), ("jumping", "🤸")], "present-cont"),
        ("Action Champion", [("running", "🏃"), ("swimming", "🏊"), ("reading", "📖"), ("cooking", "🍳"), ("painting", "🎨"), ("jumping", "🤸")], "present-cont"),
    ]),
    ("How Much, How Many", "Quantity — Magic Academy Unit 8", [
        ("The Plopster", [("bread", "🍞"), ("water", "💧"), ("apples", "🍎"), ("eggs", "🥚"), ("rice", "🍚"), ("juice", "🧃")], "quantity"),
        ("A, An, Some", [("bread", "🍞"), ("water", "💧"), ("eggs", "🥚"), ("rice", "🍚"), ("bananas", "🍌"), ("sugar", "🍬")], "quantity"),
        ("Count Them", [("apples", "🍎"), ("eggs", "🥚"), ("bananas", "🍌"), ("oranges", "🍊"), ("pears", "🍐"), ("grapes", "🍇")], "quantity"),
        ("Plopster Asleep", [("water", "💧"), ("juice", "🧃"), ("rice", "🍚"), ("sugar", "🍬"), ("bread", "🍞"), ("milk", "🥛")], "quantity"),
        ("Some or Any?", [("apples", "🍎"), ("rice", "🍚"), ("juice", "🧃"), ("eggs", "🥚"), ("sugar", "🍬"), ("milk", "🥛")], "quantity"),
        ("Wake the Plopster", [("juice", "🧃"), ("water", "💧"), ("milk", "🥛"), ("sugar", "🍬"), ("rice", "🍚"), ("bread", "🍞")], "quantity"),
        ("Where's the Egg?", [("egg", "🥚"), ("box", "📦"), ("cup", "☕"), ("bag", "🎒"), ("table", "🪑"), ("chair", "🪑")], "quantity"),
        ("Big Letters", [("Tel Aviv", "🌆"), ("Mina", "👧"), ("Mom", "👩"), ("Lila", "🌸"), ("school", "🏫"), ("home", "🏠")], "quantity"),
        ("Sound Lab", [("blonde", "💛"), ("flower", "🌸"), ("glove", "🧤"), ("plate", "🍽️"), ("glass", "🫙"), ("clock", "🕐")], "quantity"),
        ("Quantity Champion", [("apples", "🍎"), ("water", "💧"), ("eggs", "🥚"), ("rice", "🍚"), ("juice", "🧃"), ("sugar", "🍬")], "quantity"),
    ]),
    ("Let's Compare", "Comparatives — Magic Academy Unit 9", [
        ("The Empty Zoo", [("lion", "🦁"), ("cat", "🐱"), ("rabbit", "🐰"), ("turtle", "🐢"), ("giraffe", "🦒"), ("mouse", "🐭")], "comparative"),
        ("The Fireflies", [("lion", "🦁"), ("cat", "🐱"), ("rabbit", "🐰"), ("turtle", "🐢"), ("giraffe", "🦒"), ("mouse", "🐭")], "comparative"),
        ("Bigger Than", [("lion", "🦁"), ("cat", "🐱"), ("rabbit", "🐰"), ("turtle", "🐢"), ("giraffe", "🦒"), ("mouse", "🐭")], "comparative"),
        ("Spelling Rules", [("big", "🐘"), ("small", "🐜"), ("fast", "🚀"), ("slow", "🐌"), ("tall", "🌳"), ("short", "🧑")], "comparative"),
        ("Better or Worse", [("good", "👍"), ("bad", "👎"), ("big", "🐘"), ("small", "🐜"), ("long", "📏"), ("short", "🧑")], "comparative"),
        ("More Beautiful", [("beautiful", "🌸"), ("interesting", "🔍"), ("dangerous", "⚠️"), ("friendly", "🤝"), ("careful", "🧠"), ("noisy", "🔊")], "comparative"),
        ("Slime Maker", [("Spain", "🇪🇸"), ("France", "🇫🇷"), ("Israel", "🇮🇱"), ("Japan", "🇯🇵"), ("Brazil", "🇧🇷"), ("India", "🇮🇳")], "comparative"),
        ("The Talking Bubbles", [("lion", "🦁"), ("cat", "🐱"), ("rabbit", "🐰"), ("turtle", "🐢"), ("giraffe", "🦒"), ("mouse", "🐭")], "comparative"),
        ("Sound Lab", [("twins", "👯"), ("smile", "😊"), ("spark", "✨"), ("spoon", "🥄"), ("swim", "🏊"), ("train", "🚆")], "comparative"),
        ("Compare Champion", [("lion", "🦁"), ("cat", "🐱"), ("rabbit", "🐰"), ("turtle", "🐢"), ("giraffe", "🦒"), ("mouse", "🐭")], "comparative"),
    ]),
    ("Places & Past", "Was / were — Magic Academy Unit 10", [
        ("Don't Look at the Slime", [("school", "🏫"), ("park", "🏞️"), ("shop", "🏪"), ("bus", "🚌"), ("car", "🚗"), ("train", "🚆")], "was-were"),
        ("The Shrinking Machine", [("school", "🏫"), ("park", "🏞️"), ("shop", "🏪"), ("bus", "🚌"), ("car", "🚗"), ("train", "🚆")], "was-were"),
        ("Not There", [("school", "🏫"), ("park", "🏞️"), ("shop", "🏪"), ("bus", "🚌"), ("car", "🚗"), ("train", "🚆")], "was-were"),
        ("The Slime Empire", [("school", "🏫"), ("park", "🏞️"), ("shop", "🏪"), ("bus", "🚌"), ("car", "🚗"), ("train", "🚆")], "was-were"),
        ("There Was a Slime", [("school", "🏫"), ("park", "🏞️"), ("shop", "🏪"), ("bus", "🚌"), ("car", "🚗"), ("train", "🚆")], "was-were"),
        ("Giving Directions", [("left", "⬅️"), ("right", "➡️"), ("next to", "➡️"), ("under", "🔽"), ("on", "📍"), ("in", "📦")], "was-were"),
        ("Yesterday", [("school", "🏫"), ("park", "🏞️"), ("shop", "🏪"), ("bus", "🚌"), ("car", "🚗"), ("train", "🚆")], "was-were"),
        ("Novus Comes to Help", [("school", "🏫"), ("park", "🏞️"), ("shop", "🏪"), ("bus", "🚌"), ("car", "🚗"), ("train", "🚆")], "was-were"),
        ("Sound Lab", [("school", "🏫"), ("park", "🏞️"), ("shop", "🏪"), ("bus", "🚌"), ("car", "🚗"), ("train", "🚆")], "was-were"),
        ("Grand Grammar Finale", [("school", "🏫"), ("park", "🏞️"), ("shop", "🏪"), ("bus", "🚌"), ("car", "🚗"), ("train", "🚆")], "was-were"),
    ]),
]

ADVANCED_WORLDS = [
    ("Tense Trek", "Verb forms across time", [
        ("Past simple regular verbs", [("played", "🏏"), ("jumped", "🤾"), ("cooked", "🍳"), ("cleaned", "🧹"), ("watched", "🎬"), ("helped", "🆘")]),
        ("Past simple irregular verbs", [("went", "🚶"), ("ate", "🍽️"), ("saw", "👁️"), ("had", "🍎"), ("took", "📸"), ("made", "🔨")]),
        ("Past continuous tense", [("running", "🏃"), ("swimming", "🏊"), ("dancing", "💃"), ("painting", "🎨"), ("reading", "📖"), ("singing", "🎤")]),
        ("Present perfect tense", [("visited", "🏠"), ("learned", "🧠"), ("started", "🏁"), ("finished", "✅"), ("tried", "🧪"), ("found", "🔎")]),
        ("Past perfect tense", [("had", "🍎"), ("seen", "👀"), ("gone", "✈️"), ("eaten", "🍔"), ("made", "🔨"), ("done", "✅")]),
        ("Future simple with will", [("will", "🎯"), ("plan", "🗓️"), ("help", "🤝"), ("change", "🔄"), ("share", "🤲"), ("dream", "💭")]),
        ("Future with going to", [("going", "🚗"), ("planning", "🧭"), ("traveling", "🌍"), ("saving", "💰"), ("joining", "🤝"), ("building", "🏗️")]),
        ("Present perfect continuous", [("been", "🧑‍🏫"), ("working", "💼"), ("studying", "📚"), ("waiting", "⏳"), ("playing", "🎮"), ("living", "🏠")]),
        ("Past perfect continuous", [("had", "🍎"), ("been", "🧑‍🏫"), ("sleeping", "😴"), ("running", "🏃"), ("practicing", "🎹"), ("looking", "🔍")]),
        ("Future continuous tense", [("playing", "🎾"), ("cooking", "🍳"), ("sleeping", "😴"), ("traveling", "✈️"), ("reading", "📖"), ("watching", "🎬")]),
    ]),
    ("Modal Mountain", "Can, may, must and more", [
        ("Ability: can / could", [("can", "✅"), ("could", "🤔"), ("run", "🏃"), ("jump", "🤾"), ("sing", "🎤"), ("swim", "🏊")]),
        ("Possibility: may / might", [("may", "🌧️"), ("might", "⚡"), ("rain", "🌧️"), ("snow", "❄️"), ("change", "🔄"), ("happen", "🎲")]),
        ("Obligation: must / have to", [("must", "🛑"), ("have", "🤲"), ("need", "📌"), ("finish", "✅"), ("study", "📚"), ("clean", "🧹")]),
        ("Advice: should / ought to", [("should", "💡"), ("ought", "🧠"), ("ask", "❓"), ("listen", "👂"), ("try", "🧪"), ("learn", "📘")]),
        ("Habits & past ability: would / used to", [("would", "🌀"), ("used", "🔧"), ("read", "📖"), ("play", "🎮"), ("walk", "🚶"), ("think", "💭")]),
        ("Permission and request phrases", [("please", "🙏"), ("may", "🟦"), ("can", "✅"), ("ask", "❓"), ("help", "🤝"), ("open", "🔓")]),
        ("Necessity and lack of necessity", [("must", "🛑"), ("need", "📌"), ("dont", "🚫"), ("can", "✅"), ("skip", "⏭️"), ("save", "💾")]),
        ("Polite obligation vs orders", [("please", "🙏"), ("must", "🛑"), ("should", "💡"), ("wait", "⏳"), ("stop", "✋"), ("listen", "👂")]),
        ("Modal questions and short answers", [("can", "✅"), ("could", "🤔"), ("will", "🎯"), ("yes", "👍"), ("no", "👎"), ("why", "❓")]),
        ("Mixed modal review", [("may", "🌦️"), ("must", "🛑"), ("should", "💡"), ("can", "✅"), ("might", "⚡"), ("would", "🌀")]),
    ]),
    ("Conditional Cove", "If... then... everyday facts", [
        ("Zero conditional facts", [("rain", "🌧️"), ("wet", "💧"), ("hot", "🔥"), ("cold", "❄️"), ("sleep", "😴"), ("smile", "😊")]),
        ("First conditional real future", [("if", "❓"), ("will", "🎯"), ("go", "🚶"), ("come", "🚗"), ("help", "🤝"), ("wait", "⏳")]),
        ("Second conditional unreal present", [("would", "🌀"), ("dream", "💭"), ("wish", "🌠"), ("imagine", "🧠"), ("change", "🔄"), ("travel", "✈️")]),
        ("Third conditional unreal past", [("had", "🍎"), ("known", "🧠"), ("been", "🧑‍🏫"), ("missed", "✋"), ("seen", "👀"), ("done", "✅")]),
        ("Mixed conditionals", [("if", "❓"), ("then", "➡️"), ("when", "⏰"), ("because", "🔗"), ("unless", "🚫"), ("before", "⏳")]),
        ("Conditional questions and advice", [("should", "💡"), ("could", "🤔"), ("would", "🌀"), ("ask", "❓"), ("help", "🤝"), ("listen", "👂")]),
        ("Conditional time connectives", [("when", "⏰"), ("after", "➡️"), ("before", "⏳"), ("while", "⌛"), ("then", "➡️"), ("until", "⏳")]),
        ("Conditional verbs in conversation", [("say", "🗣️"), ("tell", "📣"), ("ask", "❓"), ("answer", "✅"), ("talk", "🗨️"), ("listen", "👂")]),
        ("Conditional outcomes and consequences", [("result", "✅"), ("because", "🔗"), ("so", "➡️"), ("then", "➡️"), ("change", "🔄"), ("learn", "📘")]),
        ("Conditional review challenge", [("if", "❓"), ("then", "➡️"), ("would", "🌀"), ("must", "🛑"), ("can", "✅"), ("should", "💡")]),
    ]),
    ("Passive Place", "Passive voice and agent words", [
        ("Passive voice present simple", [("is", "🔵"), ("are", "🟢"), ("was", "🟠"), ("were", "🟣"), ("seen", "👀"), ("made", "🔨")]),
        ("Passive voice past simple", [("was", "🟠"), ("were", "🟣"), ("built", "🏗️"), ("given", "🎁"), ("found", "🔎"), ("lost", "🧭")]),
        ("Passive voice future and perfect forms", [("will", "🎯"), ("been", "🧑‍🏫"), ("be", "🔵"), ("made", "🔨"), ("seen", "👀"), ("found", "🔎")]),
        ("Passive voice with by + agent", [("by", "➡️"), ("me", "👤"), ("you", "👥"), ("them", "👥"), ("him", "👨"), ("her", "👩")]),
        ("Passive in instructions and signs", [("stop", "✋"), ("closed", "🔒"), ("open", "🔓"), ("must", "🛑"), ("keep", "🔐"), ("enter", "🚪")]),
        ("Passive with get and be", [("get", "📥"), ("got", "📦"), ("be", "🔵"), ("been", "🧑‍🏫"), ("made", "🔨"), ("seen", "👀")]),
        ("Passive in news and descriptions", [("reported", "📰"), ("opened", "🚪"), ("lost", "🧭"), ("found", "🔎"), ("called", "📞"), ("known", "🧠")]),
        ("Passive voice sentence building", [("is", "🔵"), ("was", "🟠"), ("been", "🧑‍🏫"), ("made", "🔨"), ("seen", "👀"), ("called", "📞")]),
        ("Active/passive transformation", [("make", "🔨"), ("made", "🔨"), ("see", "👀"), ("seen", "👀"), ("find", "🔎"), ("found", "🔎")]),
        ("Passive voice review", [("be", "🔵"), ("been", "🧑‍🏫"), ("was", "🟠"), ("were", "🟣"), ("is", "🔵"), ("are", "🟢")]),
    ]),
    ("Speech Street", "Reporting, clauses and polite phrases", [
        ("Reported speech statements", [("said", "🗣️"), ("told", "📣"), ("asked", "❓"), ("reported", "📰"), ("explained", "🧠"), ("mentioned", "💬")]),
        ("Reported questions", [("asked", "❓"), ("wondered", "🤔"), ("said", "🗣️"), ("why", "❓"), ("where", "📍"), ("when", "⏰")]),
        ("Reported commands and requests", [("told", "📣"), ("asked", "❓"), ("ordered", "📋"), ("please", "🙏"), ("want", "🎯"), ("need", "📌")]),
        ("Relative clauses with who / which / that", [("who", "👤"), ("which", "🔎"), ("that", "👉"), ("person", "🧍"), ("thing", "📦"), ("place", "📍")]),
        ("Defining vs non-defining relative clauses", [("my", "👤"), ("his", "👨"), ("our", "👥"), ("that", "👉"), ("which", "🔎"), ("who", "👤")]),
        ("Tag questions", [("isnt", "❓"), ("arent", "❓"), ("doesnt", "❌"), ("wont", "❓"), ("right", "👍"), ("yes", "✅")]),
        ("Direct and indirect objects", [("me", "👤"), ("him", "👨"), ("her", "👩"), ("it", "📦"), ("them", "👥"), ("us", "👥")]),
        ("Gerunds and infinitives", [("playing", "🎾"), ("to", "➡️"), ("read", "📖"), ("writing", "✍️"), ("learn", "📘"), ("singing", "🎤")]),
        ("Verbs followed by gerunds", [("enjoy", "😄"), ("avoid", "🚫"), ("finish", "✅"), ("start", "🏁"), ("hate", "😡"), ("love", "❤️")]),
        ("Verbs followed by infinitives", [("want", "🎯"), ("need", "📌"), ("hope", "🌟"), ("decide", "🧠"), ("promise", "🤝"), ("learn", "📘")]),
    ]),
    ("Structure Station", "Words and phrases that connect ideas", [
        ("Phrasal verbs with get", [("get", "📥"), ("up", "⬆️"), ("out", "🚪"), ("on", "🟢"), ("off", "🔻"), ("back", "↩️")]),
        ("Phrasal verbs with take", [("take", "✋"), ("off", "🔻"), ("out", "🚪"), ("in", "⬇️"), ("back", "↩️"), ("up", "⬆️")]),
        ("Phrasal verbs with put", [("put", "📌"), ("on", "🟢"), ("off", "🔻"), ("in", "⬇️"), ("out", "🚪"), ("away", "➡️")]),
        ("Phrasal verbs with make", [("make", "🔨"), ("up", "⬆️"), ("into", "🔁"), ("out", "🚪"), ("sure", "✅"), ("time", "⏰")]),
        ("Phrasal verbs with look", [("look", "👀"), ("after", "🛟"), ("for", "🔍"), ("up", "⬆️"), ("out", "🚪"), ("back", "↩️")]),
        ("Common idioms and expressions", [("break", "🍞"), ("fast", "⚡"), ("piece", "🧩"), ("mind", "🧠"), ("hand", "✋"), ("head", "🧢")]),
        ("Common collocations", [("make", "🔨"), ("do", "✅"), ("take", "✋"), ("have", "🤲"), ("strong", "💪"), ("heavy", "🏋️")]),
        ("Linking words and discourse markers", [("because", "🔗"), ("however", "↔️"), ("therefore", "➡️"), ("meanwhile", "⏳"), ("finally", "🏁"), ("also", "➕")]),
        ("Time expressions practice", [("yesterday", "📅"), ("today", "🗓️"), ("tomorrow", "📅"), ("ago", "⏳"), ("later", "⌛"), ("soon", "⏱️")]),
        ("Prepositions of time", [("at", "📍"), ("on", "🟦"), ("in", "🟪"), ("before", "⏳"), ("after", "➡️"), ("during", "🕒")]),
    ]),
    ("Quantifier Quay", "Space, movement and comparison", [
        ("Prepositions of place", [("in", "📦"), ("on", "📍"), ("under", "⬇️"), ("next", "➡️"), ("between", "↔️"), ("behind", "⬅️")]),
        ("Prepositions of movement", [("to", "➡️"), ("from", "⬅️"), ("across", "🌉"), ("into", "🕳️"), ("past", "🏁"), ("through", "🚪")]),
        ("Directions and giving instructions", [("left", "⬅️"), ("right", "➡️"), ("straight", "⬆️"), ("turn", "↪️"), ("stop", "✋"), ("go", "🏃")]),
        ("Expressing likes and dislikes", [("like", "👍"), ("love", "❤️"), ("hate", "👎"), ("enjoy", "😄"), ("prefer", "⭐"), ("dislike", "😠")]),
        ("Making comparisons", [("bigger", "📏"), ("smaller", "📏"), ("faster", "🚀"), ("slower", "🐢"), ("more", "➕"), ("less", "➖")]),
        ("Talking about habits and routines", [("usually", "🕒"), ("often", "🔁"), ("always", "✅"), ("never", "🚫"), ("sometimes", "⚖️"), ("rarely", "🐢")]),
        ("Describing daily schedules", [("morning", "🌅"), ("afternoon", "🌤️"), ("evening", "🌆"), ("night", "🌙"), ("breakfast", "🍳"), ("dinner", "🍽️")]),
        ("Talking about health and illnesses", [("healthy", "💚"), ("sick", "🤒"), ("doctor", "🩺"), ("medicine", "💊"), ("cough", "😷"), ("rest", "🛌")]),
        ("Food and drink vocabulary", [("bread", "🍞"), ("juice", "🧃"), ("salad", "🥗"), ("coffee", "☕"), ("cake", "🍰"), ("water", "💧")]),
        ("Cooking and recipes language", [("cook", "🍳"), ("mix", "🥣"), ("bake", "🧁"), ("chop", "🔪"), ("stir", "🥄"), ("serve", "🍽️")]),
    ]),
    ("Polite Plaza", "Social language for everyday situations", [
        ("Shopping vocabulary and phrases", [("price", "💲"), ("buy", "🛍️"), ("sell", "💰"), ("cost", "💵"), ("shop", "🏪"), ("cash", "💵")]),
        ("Money, prices, and currency", [("dollar", "💵"), ("coin", "🪙"), ("price", "💲"), ("change", "🔄"), ("pay", "💳"), ("save", "💰")]),
        ("Jobs and occupations", [("doctor", "🩺"), ("teacher", "🧑‍🏫"), ("chef", "👨‍🍳"), ("artist", "🧑‍🎨"), ("driver", "🚗"), ("builder", "👷" )]),
        ("Work and workplace vocabulary", [("office", "🏢"), ("meeting", "📅"), ("team", "👥"), ("email", "📧"), ("project", "📁"), ("break", "☕" )]),
        ("School and education vocabulary", [("lesson", "📖"), ("teacher", "🧑‍🏫"), ("student", "🧑‍🎓"), ("class", "🏫"), ("homework", "📝"), ("grade", "🅰️" )]),
        ("Degrees of certainty and possibility", [("sure", "✅"), ("maybe", "🤷"), ("certain", "📌"), ("possible", "❓"), ("surely", "🟢"), ("unlikely", "🚫" )]),
        ("Expressing preferences", [("prefer", "⭐"), ("rather", "↔️"), ("like", "👍"), ("love", "❤️"), ("hate", "👎"), ("choose", "✅" )]),
        ("Asking for and giving permission", [("can", "✅"), ("may", "🔵"), ("let", "➡️"), ("allow", "✅"), ("okay", "👌"), ("ask", "❓" )]),
        ("Making offers and suggestions", [("should", "💡"), ("could", "🤔"), ("maybe", "🤷"), ("lets", "👉"), ("try", "🧪"), ("offer", "🎁" )]),
        ("Giving and following advice", [("advice", "💬"), ("listen", "👂"), ("try", "🧪"), ("change", "🔄"), ("help", "🤝"), ("fix", "🔧" )]),
    ]),
    ("Everyday Express", "Practical phrases for daily life", [
        ("Apologizing and responding to apologies", [("sorry", "😔"), ("forgive", "🙏"), ("excuse", "🙇"), ("please", "🙏"), ("thanks", "🙏"), ("okay", "👌" )]),
        ("Asking for help and assistance", [("help", "🤝"), ("assist", "🧑‍🔧"), ("please", "🙏"), ("need", "📌"), ("support", "🛟"), ("guide", "🧭" )]),
        ("Telephone English and polite phrases", [("hello", "👋"), ("goodbye", "👋"), ("call", "📞"), ("message", "✉️"), ("ask", "❓"), ("speak", "🗣️" )]),
        ("Email and letter writing basics", [("email", "📧"), ("write", "✍️"), ("send", "📤"), ("reply", "↩️"), ("subject", "📝"), ("letter", "✉️" )]),
        ("Social expressions and small talk", [("hi", "👋"), ("bye", "👋"), ("nice", "😊"), ("yes", "✅"), ("no", "❌"), ("good", "👍" )]),
        ("Describing people: appearance and personality", [("tall", "📏"), ("short", "📏"), ("kind", "🤗"), ("shy", "😳"), ("friendly", "😊"), ("funny", "😂" )]),
        ("Family relationships vocabulary", [("mother", "👩"), ("father", "👨"), ("sister", "👧"), ("brother", "👦"), ("uncle", "🧑‍🤝‍🧑"), ("aunt", "👩‍🦳" )]),
        ("Travel vocabulary and airport phrases", [("plane", "✈️"), ("ticket", "🎫"), ("passport", "🛂"), ("luggage", "🧳"), ("flight", "🛫"), ("arrival", "🛬" )]),
        ("Hotel and accommodation phrases", [("hotel", "🏨"), ("room", "🛏️"), ("bed", "🛌"), ("bath", "🛁"), ("key", "🔑"), ("desk", "🛋️" )]),
        ("Transportation and directions", [("car", "🚗"), ("bus", "🚌"), ("train", "🚆"), ("stop", "🛑"), ("left", "⬅️"), ("right", "➡️" )]),
    ]),
    ("Big Idea Boulevard", "Broad topics and vocabulary", [
        ("Weather vocabulary and small talk", [("sunny", "☀️"), ("rainy", "🌧️"), ("cloudy", "☁️"), ("windy", "🌬️"), ("stormy", "⛈️"), ("hot", "🔥" )]),
        ("Seasons and holidays", [("spring", "🌷"), ("summer", "☀️"), ("autumn", "🍂"), ("winter", "❄️"), ("holiday", "🎉"), ("party", "🥳" )]),
        ("Sports and exercise vocabulary", [("soccer", "⚽"), ("tennis", "🎾"), ("boxing", "🥊"), ("yoga", "🧘"), ("swim", "🏊"), ("run", "🏃" )]),
        ("Hobbies and free-time activities", [("dance", "💃"), ("read", "📖"), ("paint", "🎨"), ("play", "🎮"), ("bake", "🧁"), ("garden", "🌻" )]),
        ("Music and entertainment vocabulary", [("song", "🎵"), ("movie", "🎬"), ("concert", "🎤"), ("guitar", "🎸"), ("dance", "💃"), ("show", "🎭" )]),
        ("Animals and nature vocabulary", [("forest", "🌲"), ("river", "🏞️"), ("mountain", "⛰️"), ("animal", "🐾"), ("flower", "🌸"), ("bird", "🐦" )]),
        ("Environmental issues and recycling", [("recycle", "♻️"), ("trash", "🗑️"), ("clean", "🧹"), ("earth", "🌍"), ("plastic", "🧴"), ("reuse", "🔄" )]),
        ("Technology and digital life vocabulary", [("phone", "📱"), ("computer", "💻"), ("internet", "🌐"), ("app", "📱"), ("email", "📧"), ("screen", "🖥️" )]),
        ("Science and invention vocabulary", [("experiment", "🧪"), ("robot", "🤖"), ("battery", "🔋"), ("formula", "➗"), ("idea", "💡"), ("engine", "⚙️" )]),
        ("Emotions and feelings vocabulary", [("happy", "😊"), ("sad", "😢"), ("angry", "😠"), ("excited", "🤩"), ("nervous", "😰"), ("calm", "😌" )]),
    ]),
]

SENTENCE_TEMPLATES = [
    "I like the {w}.",
    "This is my {w}.",
    "I can see the {w}.",
    "Look at the {w}!",
    "I have the {w}.",
    "The {w} is fun.",
    "My {w} is cool.",
    "Can you find the {w}?",
    "The {w} is big.",
    "I love the {w}.",
    "We have a {w}.",
    "Let's play with the {w}!",
    "I want the {w}.",
    "The {w} is nice.",
    "This is a {w}.",
    "I see a {w}.",
    "I want a {w}.",
    "The {w} is here.",
    "We can use the {w}.",
    "It is a {w}.",
]

GAME_TYPES = [
    {"id": "listen_pick_picture", "name": "Listen & Find", "instruction": "Listen, then tap the right picture!"},
    {"id": "look_pick_word", "name": "What is it?", "instruction": "Look and tap the right word!"},
    {"id": "look_pick_sound", "name": "Find the Sound", "instruction": "Tap each speaker. Which one is the picture?"},
    {"id": "match_pairs", "name": "Match It", "instruction": "Match every picture to its word!"},
    {"id": "sort_it", "name": "Sort It", "instruction": "Put each word in the right box!"},
    {"id": "build_sentence", "name": "Build a Sentence", "instruction": "Tap the words in the right order!"},
    {"id": "spell_it", "name": "Spell It", "instruction": "Tap the letters to spell the word!"},
    {"id": "true_false", "name": "Yes or No?", "instruction": "Is it right? Tap yes or no!"},
    {"id": "listen_pick_word", "name": "Listen & Read", "instruction": "Listen, then tap the right word!"},
    {"id": "pick_word_gap", "name": "Choose the Word", "instruction": "Tap the missing word!"},
    {"id": "transform", "name": "Change the Word", "instruction": "Make the right word!"},
    {"id": "fix_sentence", "name": "Fix It", "instruction": "Tap the sentence that is right!"},
    {"id": "sort_rule", "name": "Sort by Rule", "instruction": "Put each one in the right box!"},
]

PRAISE = ["Well done!", "Great job!", "Fabulous!", "Superb!", "Amazing!",
          "Excellent!", "You did it!", "Brilliant!", "Awesome!", "Perfect!",
          "Very good!", "Fantastic!", "Wonderful!", "Way to go!", "You nailed it!",
          "Incredible!", "Outstanding!", "You are awesome!", "So smart!", "Phenomenal!",
          "You rock!", "Keep it up!", "You are amazing!", "Nice work!", "That was great!"]
TRY_AGAIN = ["Try again!", "Almost!", "Oops, try again!", "Not quite!", "Have another go!"]
MASCOTS = ["🦸", "🧙", "🚀", "🌟", "🦄", "🐯", "🦉", "🤖"]


def build():
    os.makedirs(IMAGES_DIR, exist_ok=True)
    images = {}  # slug -> (emoji, color)  (first level to use a slug wins its color)
    used_asset_slugs = {}

    levels_out = []
    index = 0
    default_game_types = [
        "listen_pick_picture", "look_pick_word", "look_pick_sound", "match_pairs",
        "sort_it", "build_sentence", "spell_it", "true_false", "listen_pick_word",
        "spell_it"
    ]
    for wi, (world_name, world_sub, topics) in enumerate(WORLDS):
        for ti, (topic, words) in enumerate(topics):
            color = PALETTE[index % len(PALETTE)]
            level_id = "L%02d" % index
            items = []
            for word, emoji in words:
                slug = make_asset_slug(word, emoji, topic, used_asset_slugs)
                images.setdefault(slug, (emoji, color))
                items.append({
                    "word": word,
                    "emoji": emoji,
                    "slug": slug,
                    "image": "images/%s.svg" % slug,
                    "color": color,
                })
            sentences = []
            rng = random.Random((index + 1) * 17 + (ti + 1) * 7)
            for it in items[:min(len(items), 8)]:
                template = rng.choice(SENTENCE_TEMPLATES)
                sentences.append(template.format(w=it["word"]))
            levels_out.append({
                "id": level_id,
                "index": index,
                "world": world_name,
                "worldSubtitle": world_sub,
                "worldIndex": wi,
                "name": topic,
                "category": level_id,
                "color": color,
                "items": items,
                "sentences": sentences,
                "gameTypes": default_game_types[:],
            })
            index += 1

    for wi, (world_name, world_sub, levels) in enumerate(GRAMMAR_WORLDS, start=len(WORLDS)):
        for ti, (topic, words, theme) in enumerate(levels):
            color = PALETTE[index % len(PALETTE)]
            level_id = "L%02d" % index
            items = []
            for word, emoji in words:
                slug = make_asset_slug(word, emoji, topic, used_asset_slugs)
                images.setdefault(slug, (emoji, color))
                items.append({
                    "word": word,
                    "emoji": emoji,
                    "slug": slug,
                    "image": "images/%s.svg" % slug,
                    "color": color,
                })
            grammar = make_grammar(theme, [(it["word"], it["emoji"]) for it in items])
            if ti == 8:
                game_types = ["listen_pick_picture", "look_pick_word", "look_pick_sound", "match_pairs", "listen_pick_word", "spell_it", "spell_it", "build_sentence", "sort_it", "true_false"]
            elif ti == 9:
                game_types = ["listen_pick_picture", "look_pick_word", "pick_word_gap", "build_sentence", "sort_rule", "transform", "fix_sentence", "true_false", "spell_it", "spell_it"]
            else:
                game_types = ["listen_pick_picture", "look_pick_word", "pick_word_gap", "build_sentence", "sort_rule", "transform", "fix_sentence", "true_false", "spell_it", "spell_it"]
            sentences = make_sentences([(it["word"], it["emoji"]) for it in items], base=[
                "This is my %s." % items[0]["word"] if items else "This is my word.",
                "These are my %ss." % items[1]["word"] if len(items) > 1 else "These are my books.",
                "Can you %s?" % items[2]["word"] if len(items) > 2 else "Can you swim?"
            ])
            levels_out.append({
                "id": level_id,
                "index": index,
                "world": world_name,
                "worldSubtitle": world_sub,
                "worldIndex": wi,
                "name": topic,
                "category": level_id,
                "color": color,
                "items": items,
                "sentences": sentences,
                "grammar": grammar,
                "gameTypes": game_types,
            })
            index += 1

    for wi, (world_name, world_sub, topics) in enumerate(ADVANCED_WORLDS, start=len(WORLDS) + len(GRAMMAR_WORLDS)):
        for ti, (topic, words) in enumerate(topics):
            color = PALETTE[index % len(PALETTE)]
            level_id = "L%02d" % index
            items = []
            for word, emoji in words:
                slug = make_asset_slug(word, emoji, topic, used_asset_slugs)
                images.setdefault(slug, (emoji, color))
                items.append({
                    "word": word,
                    "emoji": emoji,
                    "slug": slug,
                    "image": "images/%s.svg" % slug,
                    "color": color,
                })
            sentences = []
            rng = random.Random((index + 1) * 17 + (ti + 1) * 7)
            for it in items[:min(len(items), 8)]:
                template = rng.choice(SENTENCE_TEMPLATES)
                sentences.append(template.format(w=it["word"]))
            levels_out.append({
                "id": level_id,
                "index": index,
                "world": world_name,
                "worldSubtitle": world_sub,
                "worldIndex": wi,
                "name": topic,
                "category": level_id,
                "color": color,
                "items": items,
                "sentences": sentences,
                "gameTypes": default_game_types[:],
            })
            index += 1

    model = {
        "meta": {
            "title": "Magic Academy: English Quest",
            "tagline": "Learn English the fun way!",
            "gamesPerSession": 10,
            "maxSessionScore": 100,
            "unlockScore": 95,
            "totalLevels": len(levels_out),
            "audio": "Web Speech API (en-US / American accent)",
        },
        "praise": PRAISE,
        "tryAgain": TRY_AGAIN,
        "mascots": MASCOTS,
        "gameTypes": GAME_TYPES,
        "levels": levels_out,
    }

    with open(os.path.join(HERE, "content.json"), "w", encoding="utf-8") as f:
        json.dump(model, f, ensure_ascii=False, indent=2)

    with open(os.path.join(HERE, "data.js"), "w", encoding="utf-8") as f:
        f.write("/* AUTO-GENERATED by build_assets.py — do not edit by hand. */\n")
        f.write("window.GAME_DATA = ")
        json.dump(model, f, ensure_ascii=False, indent=2)
        f.write(";\n")

    emoji_font = "Apple Color Emoji, Segoe UI Emoji, Noto Color Emoji, sans-serif"
    for slug, (emoji, color) in images.items():
        svg = (
            '<svg xmlns="http://www.w3.org/2000/svg" width="240" height="240" '
            'viewBox="0 0 240 240" role="img" aria-label="%s">\n'
            '  <rect x="10" y="10" width="220" height="220" rx="30" '
            'fill="%s" stroke="#1b1240" stroke-width="7"/>\n'
            '  <text x="120" y="128" font-size="132" text-anchor="middle" '
            'dominant-baseline="central" font-family="%s">%s</text>\n'
            '</svg>\n'
        ) % (slug, color, emoji_font, emoji)
        with open(os.path.join(IMAGES_DIR, "%s.svg" % slug), "w", encoding="utf-8") as f:
            f.write(svg)

    print("Generated content.json, data.js and %d images." % len(images))
    print("Worlds: %d   Levels: %d" % (len(WORLDS) + len(GRAMMAR_WORLDS) + len(ADVANCED_WORLDS), len(levels_out)))


if __name__ == "__main__":
    build()
