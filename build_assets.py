#!/usr/bin/env python3
"""
build_assets.py  —  Magic Academy: English Quest
=================================================
Single source of truth for ALL game content (now ~100 levels).

    python3 build_assets.py

Outputs (next to this file):
    content.json      Pretty structured data file (the canonical curriculum).
    data.js           `window.GAME_DATA = {...}` — loaded by the browser.
    images/<slug>.svg One small, colourful picture per vocabulary word.

Curriculum
----------
Content is organised into "worlds" that mirror the real Novakid ladder
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
  matching emoji on a coloured card, referenced by each item's `image` field.
  The app falls back to a live emoji if a file is missing, so pictures never
  break. Colours cycle per level for variety.
* Audio: generated live in the browser by the Web Speech API with an en-US
  (American) voice — see app.js. No audio files are shipped.
"""

import json
import os
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


# ---------------------------------------------------------------------------
# WORLDS -> LEVELS -> (word, emoji)
# Each level: (topic name, [(word, emoji), ...]). >= 5 words so every game
# (which needs 4 options / 4 pairs) always has enough material.
# ---------------------------------------------------------------------------
WORLDS = [
    ("Pre-K Planet", "First tiny words", [
        ("Colours", [("red", "🔴"), ("blue", "🔵"), ("green", "🟢"), ("yellow", "🟡"), ("orange", "🟠"), ("purple", "🟣"), ("pink", "🩷"), ("black", "⚫")]),
        ("Numbers 1-5", [("one", "1️⃣"), ("two", "2️⃣"), ("three", "3️⃣"), ("four", "4️⃣"), ("five", "5️⃣")]),
        ("Numbers 6-10", [("six", "6️⃣"), ("seven", "7️⃣"), ("eight", "8️⃣"), ("nine", "9️⃣"), ("ten", "🔟")]),
        ("Shapes", [("star", "⭐"), ("heart", "❤️"), ("circle", "⚪"), ("square", "🟦"), ("diamond", "💎"), ("moon", "🌙")]),
        ("Pets", [("cat", "🐱"), ("dog", "🐶"), ("fish", "🐟"), ("rabbit", "🐰"), ("bird", "🐦"), ("mouse", "🐭")]),
        ("Farm Animals", [("cow", "🐮"), ("pig", "🐷"), ("horse", "🐴"), ("sheep", "🐑"), ("duck", "🦆"), ("hen", "🐔")]),
        ("My Body", [("hand", "✋"), ("eye", "👁️"), ("nose", "👃"), ("ear", "👂"), ("mouth", "👄"), ("foot", "🦶")]),
        ("Fruit", [("apple", "🍎"), ("banana", "🍌"), ("orange", "🍊"), ("grapes", "🍇"), ("strawberry", "🍓"), ("melon", "🍉")]),
        ("Toys", [("ball", "⚽"), ("teddy", "🧸"), ("doll", "🪆"), ("car", "🚗"), ("kite", "🪁"), ("blocks", "🧱")]),
        ("Family", [("mum", "👩"), ("dad", "👨"), ("baby", "👶"), ("brother", "👦"), ("sister", "👧"), ("grandma", "👵"), ("grandpa", "👴")]),
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
        ("Colours 2", [("pink", "🩷"), ("brown", "🤎"), ("white", "⚪"), ("black", "⚫"), ("grey", "🩶"), ("blue", "🔵")]),
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

SENTENCE_TEMPLATES = ["I like the {w}.", "This is my {w}.", "I can see the {w}.", "Look at the {w}!", "I have the {w}."]

GAME_TYPES = [
    {"id": "listen_pick_picture", "name": "Listen & Find", "instruction": "Listen, then tap the right picture!"},
    {"id": "look_pick_word", "name": "What is it?", "instruction": "Look and tap the right word!"},
    {"id": "look_pick_sound", "name": "Find the Sound", "instruction": "Tap each speaker. Which one is the picture?"},
    {"id": "match_pairs", "name": "Match It", "instruction": "Match every picture to its word!"},
    {"id": "sort_it", "name": "Sort It", "instruction": "Put each word in the right box!"},
    {"id": "say_it", "name": "Say It", "instruction": "Tap the microphone and say the word!"},
    {"id": "build_sentence", "name": "Build a Sentence", "instruction": "Tap the words in the right order!"},
    {"id": "spell_it", "name": "Spell It", "instruction": "Tap the letters to spell the word!"},
    {"id": "true_false", "name": "Yes or No?", "instruction": "Is it right? Tap yes or no!"},
    {"id": "listen_pick_word", "name": "Listen & Read", "instruction": "Listen, then tap the right word!"},
]

PRAISE = ["Well done!", "Great job!", "Fabulous!", "Superb!", "Amazing!",
          "Excellent!", "You did it!", "Brilliant!", "Awesome!", "Perfect!",
          "Very good!", "Fantastic!", "Wonderful!", "Way to go!"]
TRY_AGAIN = ["Try again!", "Almost!", "Oops, try again!", "Not quite!", "Have another go!"]
MASCOTS = ["🦸", "🧙", "🚀", "🌟", "🦄", "🐯", "🦉", "🤖"]


def build():
    os.makedirs(IMAGES_DIR, exist_ok=True)
    images = {}  # slug -> (emoji, color)  (first level to use a slug wins its colour)

    levels_out = []
    index = 0
    for wi, (world_name, world_sub, topics) in enumerate(WORLDS):
        for ti, (topic, words) in enumerate(topics):
            color = PALETTE[index % len(PALETTE)]
            level_id = "L%02d" % index
            items = []
            for word, emoji in words:
                slug = slugify(word)
                images.setdefault(slug, (emoji, color))
                items.append({
                    "word": word,
                    "emoji": emoji,
                    "slug": slug,
                    "image": "images/%s.svg" % slug,
                    "color": color,
                })
            # auto-generate short, valid sentences from the first words
            sentences = []
            for i, it in enumerate(items[:len(SENTENCE_TEMPLATES)]):
                s = SENTENCE_TEMPLATES[i].format(w=it["word"])
                sentences.append(s)
            levels_out.append({
                "id": level_id,
                "index": index,
                "world": world_name,
                "worldSubtitle": world_sub,
                "worldIndex": wi,
                "name": topic,
                "category": level_id,     # unique per level (used for Sort It bins)
                "color": color,
                "items": items,
                "sentences": sentences,
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
    print("Worlds: %d   Levels: %d" % (len(WORLDS), len(levels_out)))


if __name__ == "__main__":
    build()
