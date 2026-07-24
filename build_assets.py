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


def naive_plural(word):
    w = word.lower().rstrip()
    if w.endswith(("s", "x", "z", "ch", "sh")):
        return w + "s"
    if w.endswith("y") and len(w) > 1 and w[-2] not in "aeiou":
        return w[:-1] + "ys"
    return w + "es"
    if w.endswith("y") and len(w) > 1 and w[-2] not in "aeiou":
        return w[:-1] + "ies"
    return w + "s"


ADJECTIVE_WORDS = {
    "red", "blue", "green", "yellow", "orange", "purple", "pink", "black",
    "brown", "white", "gray", "grey", "sunny", "rainy", "snowy", "cloudy",
    "windy", "stormy", "hot", "cold", "happy", "sad", "angry", "sleepy",
    "scared", "surprised", "excited", "tired", "hungry", "thirsty", "bored",
    "shy", "proud", "nervous", "silly", "healthy", "sick", "hungry", "thirsty",
    "funny", "kind", "quiet", "noisy", "strong", "weak",
}
VERB_WORDS = {
    "run", "jump", "walk", "swim", "climb", "dance", "sing", "draw", "read",
    "play", "eat", "wake", "wash", "go", "ride", "cook", "paint", "watch",
    "help", "study", "learn", "listen", "ask", "tell", "say", "write", "send",
    "speak", "make", "do", "take", "put", "look", "buy", "sell", "pay", "save",
    "need", "want", "like", "love", "hate", "enjoy", "prefer", "avoid", "choose",
    "decide", "promise", "hope", "change", "join", "build", "travel", "drive", "fly",
    "box", "ski", "skate", "surf", "cycle", "order", "open", "close", "call",
    "see", "hear", "stop", "start", "continue", "wait", "work", "write", "watch",
    "play", "paint", "cook", "search", "find", "remember", "forget", "help",
}
FUNCTION_WORDS = {
    "can", "can't", "cannot", "may", "might", "must", "should", "ought", "would",
    "will", "shall", "have", "has", "had", "do", "does", "did", "is", "are",
    "was", "were", "not", "please", "let", "let's", "yes", "no",
}
NUMBER_WORDS = {"one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten"}
PLURAL_EXCEPTIONS = {"yes", "this", "his", "as", "was", "is", "has", "does", "goes", "lets", "us", "plus", "minus"}


def article_for(word):
    w = word.lower().strip()
    return "an" if re.match(r"^[aeiou]", w) else "a"


UNCOUNTABLE_WORDS = {
    "water", "rice", "sugar", "juice", "milk", "bread", "coffee", "tea",
    "meat", "information", "furniture", "music", "homework",
}


def third_person_s(word):
    w = word.lower().strip()
    if w.endswith(("s", "x", "z", "ch", "sh")):
        return w + "es"
    if w.endswith("y") and len(w) > 1 and w[-2] not in "aeiou":
        return w[:-1] + "ies"
    return w + "s"


def make_sentences(items, base=None):
    base = base or []
    sentences = []
    sentence_map = {}

    def add_sentence(text, word):
        if text in sentences:
            idx = sentences.index(text)
        else:
            idx = len(sentences)
            sentences.append(text)
        sentence_map.setdefault(word, []).append(idx)

    def categorize(word):
        w = word.lower().strip()
        if w in FUNCTION_WORDS:
            return "function"
        if w in NUMBER_WORDS or w.isdigit():
            return "number"
        if " " in w:
            parts = w.split()
            if parts[0] in VERB_WORDS or parts[-1] in {"up", "down", "in", "out", "on", "off", "away", "back"}:
                return "verb"
            return "phrase"
        if w.endswith("ing"):
            return "ing"
        if w in ADJECTIVE_WORDS:
            return "adjective"
        if w.endswith("s") and w not in PLURAL_EXCEPTIONS:
            return "plural"
        if w in VERB_WORDS:
            return "verb"
        return "noun"

    def build_templates(word, category):
        if category == "adjective":
            return [
                "The %s one is nice." % word,
                "I like the %s one." % word,
                "It is %s." % word,
                "This is very %s." % word,
                "Can you see the %s one?" % word,
                "The %s color is pretty." % word,
            ]
        if category == "verb":
            return [
                "I can %s." % word,
                "Can you %s?" % word,
                "We %s today." % word,
                "She can %s." % word,
                "Let's %s." % word,
            ]
        if category == "ing":
            return [
                "I am %s." % word,
                "We are %s." % word,
                "She is %s." % word,
                "They are %s." % word,
                "Can you %s?" % word,
            ]
        if category == "function":
            return [
                "Please say %s." % word,
                "Say %s." % word,
                "This is %s." % word,
                "I want %s." % word,
            ]
        if category == "number":
            return [
                "I see %s." % word,
                "There are %s." % word,
                "Count %s." % word,
                "This is %s." % word,
            ]
        if category == "plural":
            return [
                "These are %s." % word,
                "I like %s." % word,
                "Can you see %s?" % word,
                "I see %s." % word,
            ]
        if category == "phrase":
            return [
                "This is %s." % word,
                "I like %s." % word,
                "Can you see %s?" % word,
                "I want %s." % word,
            ]
        return [
            "This is %s %s." % (article_for(word), word),
            "I like the %s." % word,
            "I can see the %s." % word,
            "Look at the %s!" % word,
            "My %s is here." % word,
            "The %s is nice." % word,
            "I want the %s." % word,
            "Let's play with the %s." % word,
        ]

    for word, _ in items:
        category = categorize(word)
        templates = build_templates(word, category)
        for text in templates[:3]:
            add_sentence(text, word)

    for text in base:
        if text not in sentences:
            sentences.append(text)

    return sentences, sentence_map


# ---------------------------------------------------------------------------
# WORLDS -> LEVELS -> (word, emoji)
# Each level: (topic name, [(word, emoji), ...]). >= 5 words so every game
# (which needs 4 options / 4 pairs) always has enough material.
# ---------------------------------------------------------------------------
WORLDS = [
    ("ABC Alphabet", "Letters, sounds and words", [
        ("ABC A-F", [("A", "🔤"), ("B", "🔤"), ("C", "🔤"), ("D", "🔤"), ("E", "🔤"), ("F", "🔤")]),
        ("ABC G-L", [("G", "🔤"), ("H", "🔤"), ("I", "🔤"), ("J", "🔤"), ("K", "🔤"), ("L", "🔤")]),
        ("ABC M-R", [("M", "🔤"), ("N", "🔤"), ("O", "🔤"), ("P", "🔤"), ("Q", "🔤"), ("R", "🔤")]),
        ("ABC S-X", [("S", "🔤"), ("T", "🔤"), ("U", "🔤"), ("V", "🔤"), ("W", "🔤"), ("X", "🔤")]),
        ("ABC Y-Z + review", [("Y", "🔤"), ("Z", "🔤"), ("A", "🔤"), ("B", "🔤"), ("C", "🔤"), ("D", "🔤")]),
    ]),
    ("Pre-K Planet", "First tiny words", [
        ("Colors", [("red", "🔴"), ("blue", "🔵"), ("green", "🟢"), ("yellow", "🟡"), ("orange", "🟠"), ("purple", "🟣"), ("pink", "🌸"), ("black", "⚫")]),
        ("Numbers 1-5", [("one", "1️⃣"), ("two", "2️⃣"), ("three", "3️⃣"), ("four", "4️⃣"), ("five", "5️⃣")]),
        ("Numbers 6-10", [("six", "6️⃣"), ("seven", "7️⃣"), ("eight", "8️⃣"), ("nine", "9️⃣"), ("ten", "🔟")]),
        ("Shapes", [("star", "⭐"), ("heart", "❤️"), ("circle", "⚪"), ("square", "🟦"), ("diamond", "💎"), ("moon", "🌙")]),
        ("Pets", [("cat", "🐱"), ("dog", "🐶"), ("fish", "🐟"), ("rabbit", "🐰"), ("bird", "🐦"), ("mouse", "🐭")]),
        ("Farm Animals", [("cow", "🐮"), ("pig", "🐷"), ("horse", "🐴"), ("sheep", "🐑"), ("duck", "🦆"), ("hen", "🐔")]),
        ("My Body", [("hand", "✋"), ("eye", "👁️"), ("nose", "👃"), ("ear", "👂"), ("mouth", "👄"), ("foot", "🦶")]),
        ("Fruit", [("apple", "🍎"), ("banana", "🍌"), ("orange", "🍊"), ("grapes", "🍇"), ("strawberry", "🍓"), ("watermelon", "🍉")]),
        ("Toys", [("ball", "⚽"), ("teddy bear", "🧸"), ("doll", "🪆"), ("car", "🚗"), ("kite", "🪁"), ("blocks", "🧱")]),
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
    {"id": "say_it", "name": "Say It", "instruction": "Tap the mic and say the word!"},
    {"id": "true_false", "name": "Yes or No?", "instruction": "Is it right? Tap yes or no!"},
    {"id": "listen_pick_word", "name": "Listen & Read", "instruction": "Listen, then tap the right word!"},
    {"id": "pick_word_gap", "name": "Choose the Word", "instruction": "Tap the missing word!"},
    {"id": "transform", "name": "Change the Word", "instruction": "Make the right word!"},
    {"id": "fix_sentence", "name": "Fix It", "instruction": "Tap the sentence that is right!"},
    {"id": "sort_rule", "name": "Sort by Rule", "instruction": "Put each one in the right box!"},
    {"id": "tap_word", "name": "Find the Mistake", "instruction": "Tap the word that is wrong!"},
    {"id": "phrase_pair", "name": "Question & Answer", "instruction": "Match each question to its answer!"},
    {"id": "listen_sentence", "name": "Listen & Choose", "instruction": "Listen, then tap the sentence you hear!"},
]

# A grammar level plays 10 varied games so the child HEARS, READS, SPEAKS and
# UNDERSTANDS the structure — not just four tap-choice games. Order is shuffled
# by the engine each session.
GRAMMAR_RECIPE = [
    "listen_pick_word",   # hear the key word + read it (pictures speak)
    "pick_word_gap",      # grammar: choose the correct word for the blank
    "build_sentence",     # read + put the words in the right order
    "sort_rule",          # grammar: sort by rule (two labelled bins)
    "transform",          # grammar: make the right form
    "fix_sentence",       # grammar: pick the sentence that is right
    "tap_word",           # grammar: find the one wrong word
    "phrase_pair",        # conversation: match question to answer
    "listen_sentence",    # hear a whole sentence and pick it (listening)
    "spell_it",           # read + spell a key word
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
        is_abc_world = world_name == "ABC Alphabet"
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
            sentences, sentence_map = make_sentences([(it["word"], it["emoji"]) for it in items])
            level_dict = {
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
                "sentenceMap": sentence_map,
                "gameTypes": default_game_types[:],
            }
            if is_abc_world:
                level_dict["isABC"] = True
            levels_out.append(level_dict)
            index += 1

    # ---- Grammar levels (indices 100+) ----
    # Every grammar level is hand-authored (see grammar_content.py) so the English
    # is always correct. Each carries a full grammar block (gap/transform/fix/sort/
    # pairs) + clean example sentences, and plays the rich 10-game GRAMMAR_RECIPE.
    import grammar_content
    for wi, world in enumerate(grammar_content.WORLDS, start=len(WORLDS)):
        for lv in world["levels"]:
            color = PALETTE[index % len(PALETTE)]
            level_id = "L%02d" % index
            items = []
            for word, emoji in lv["items"]:
                slug = make_asset_slug(word, emoji, lv["name"], used_asset_slugs)
                images.setdefault(slug, (emoji, color))
                items.append({
                    "word": word,
                    "emoji": emoji,
                    "slug": slug,
                    "image": "images/%s.svg" % slug,
                    "color": color,
                })
            grammar = {
                "target": lv["target"],
                "gap": lv["gap"],
                "transform": lv["transform"],
                "fix": lv["fix"],
                "sort": lv["sort"],
                "pairs": lv["pairs"],
            }
            levels_out.append({
                "id": level_id,
                "index": index,
                "world": world["world"],
                "worldSubtitle": world["sub"],
                "worldIndex": wi,
                "name": lv["name"],
                "category": level_id,
                "color": color,
                "items": items,
                "sentences": lv["sentences"],
                "grammar": grammar,
                "gameTypes": GRAMMAR_RECIPE[:],
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

    import grammar_content as _gc
    print("Generated content.json, data.js and %d images." % len(images))
    print("Worlds: %d   Levels: %d" % (len(WORLDS) + len(_gc.WORLDS), len(levels_out)))


if __name__ == "__main__":
    build()
