# -*- coding: utf-8 -*-
"""
Hand-authored grammar content for Magic Academy: English Quest.

Levels 101-300 (global index 100-299) teach GRAMMAR. Unlike the vocabulary
levels (1-100), every one of these is written out by hand here so the English
is always correct — no templates that could invent wrong sentences.

Each level supplies:
  items      : >=6 (word, emoji) pairs — used by the hear / speak / spell games.
  target     : short spoken label of the grammar point.
  sentences  : 5-6 SHORT, correct example sentences (used by Build a Sentence).
  gap        : >=3 fill-the-blank items (Choose the Word).
  transform  : >=3 make-the-right-form items (Change the Word).
  fix        : >=3 right-vs-wrong sentence pairs (Fix It + Find the Mistake).
  sort       : two labelled bins + >=6 tokens, >=2 per bin (Sort by Rule).
  pairs      : >=3 question -> answer pairs (Question & Answer).

The helpers below take the CORRECT ANSWER AS A STRING (not an index) so a typo
can never silently point at the wrong option — g()/t() look up the index and
assert the answer is actually one of the options.
"""


from grammar_helpers import g, t, f, tok, srt, qa, L, W


# ===========================================================================
# WORLD 11 — Unit 1 · Digital Classroom  (Levels 101-110)
# Grammar arc: this/that/these/those, a/an, singular <-> plural, "What is this?"
# ===========================================================================
WORLD_01 = W("Digital Classroom", "This & These — Magic Academy Unit 1", [
    L("The Alien Princess",
      [("pen", "🖊️"), ("book", "📕"), ("bag", "🎒"), ("desk", "🪑"), ("ruler", "📏"), ("apple", "🍎")],
      "This is a / an",
      ["This is a pen.", "This is a book.", "This is an apple.", "That is my bag.", "This is a desk."],
      [g("This is ___ pen.", ["a", "an"], "a", "🖊️"),
       g("This is ___ apple.", ["a", "an"], "an", "🍎"),
       g("This is ___ book.", ["a", "an"], "a", "📕"),
       g("___ is a ruler.", ["This", "These"], "This", "📏")],
      [t("one pen -> many...?", "pen", ["pens", "penes", "pen"], "pens"),
       t("one book -> many...?", "book", ["bookes", "books", "book"], "books"),
       t("one apple -> many...?", "apple", ["appls", "apples", "apple"], "apples")],
      [f("This is a pen.", "This is an pen.", "🖊️"),
       f("This is an apple.", "This is a apple.", "🍎"),
       f("This is a book.", "This is an book.", "📕")],
      srt("a", "an",
          [tok("pen", "A", "🖊️"), tok("book", "A", "📕"), tok("desk", "A", "🪑"),
           tok("apple", "B", "🍎"), tok("egg", "B", "🥚"), tok("orange", "B", "🍊")]),
      [qa("What is this?", "It is a pen."),
       qa("Is this an apple?", "Yes, it is."),
       qa("Is this a book?", "No, it is a bag."),
       qa("What are these?", "They are books.")]),

    L("A or An?",
      [("apple", "🍎"), ("egg", "🥚"), ("orange", "🍊"), ("umbrella", "☔"), ("ant", "🐜"), ("book", "📕")],
      "a vs an",
      ["This is an egg.", "This is an orange.", "This is a book.", "This is an umbrella.", "That is an ant."],
      [g("I see ___ egg.", ["a", "an"], "an", "🥚"),
       g("I see ___ orange.", ["a", "an"], "an", "🍊"),
       g("I see ___ book.", ["a", "an"], "a", "📕"),
       g("I see ___ umbrella.", ["a", "an"], "an", "☔")],
      [t("one egg -> many...?", "egg", ["eggs", "egges", "egg"], "eggs"),
       t("one orange -> many...?", "orange", ["oranges", "orangs", "orange"], "oranges"),
       t("one ant -> many...?", "ant", ["antes", "ants", "ant"], "ants")],
      [f("This is an egg.", "This is a egg.", "🥚"),
       f("This is a book.", "This is an book.", "📕"),
       f("This is an umbrella.", "This is a umbrella.", "☔")],
      srt("a", "an",
          [tok("book", "A", "📕"), tok("pen", "A", "🖊️"), tok("desk", "A", "🪑"),
           tok("egg", "B", "🥚"), tok("apple", "B", "🍎"), tok("orange", "B", "🍊")]),
      [qa("What is this?", "It is an egg."),
       qa("Is this an orange?", "Yes, it is."),
       qa("Is this an apple or a book?", "It is an apple."),
       qa("What do you see?", "I see an ant.")]),

    L("Through the Portal",
      [("book", "📕"), ("pencil", "✏️"), ("desk", "🪑"), ("bag", "🎒"), ("chair", "🪑"), ("tablet", "📱")],
      "These are (plural)",
      ["These are books.", "These are pencils.", "These are my bags.", "These are chairs.", "These are tablets."],
      [g("These ___ books.", ["are", "is"], "are", "📕"),
       g("These are ___.", ["pencils", "pencil"], "pencils", "✏️"),
       g("___ are my chairs.", ["These", "This"], "These", "🪑")],
      [t("one book -> many...?", "book", ["books", "bookes", "book"], "books"),
       t("one pencil -> many...?", "pencil", ["pencils", "penciles", "pencil"], "pencils"),
       t("one tablet -> many...?", "tablet", ["tablets", "tabletes", "tablet"], "tablets")],
      [f("These are books.", "These is books.", "📕"),
       f("These are pencils.", "These are pencil.", "✏️"),
       f("These are chairs.", "This are chairs.", "🪑")],
      srt("one", "many",
          [tok("a book", "A", "📕"), tok("a pencil", "A", "✏️"), tok("a chair", "A", "🪑"),
           tok("two books", "B", "📕"), tok("three pencils", "B", "✏️"), tok("four chairs", "B", "🪑")]),
      [qa("What are these?", "They are books."),
       qa("Are these pencils?", "Yes, they are."),
       qa("Are these chairs?", "Yes, they are."),
       qa("How many books?", "Two books.")]),

    L("Near & Far",
      [("bag", "🎒"), ("board", "📋"), ("desk", "🪑"), ("chair", "🪑"), ("pen", "🖊️"), ("ruler", "📏")],
      "this vs that",
      ["This is my bag.", "That is a board.", "This is a pen.", "That is my desk.", "This is a ruler."],
      [g("___ is my bag. (here)", ["This", "That"], "This", "🎒"),
       g("___ is a board. (far)", ["That", "This"], "That", "📋"),
       g("___ is a pen. (here)", ["This", "That"], "This", "🖊️")],
      [t("one bag -> many...?", "bag", ["bags", "bages", "bag"], "bags"),
       t("one desk -> many...?", "desk", ["deskes", "desks", "desk"], "desks"),
       t("one ruler -> many...?", "ruler", ["rulers", "rulor", "ruler"], "rulers")],
      [f("This is my bag.", "This are my bag.", "🎒"),
       f("That is a board.", "That is an board.", "📋"),
       f("This is a pen.", "This is pen.", "🖊️")],
      srt("this (here)", "that (far)",
          [tok("this bag", "A", "🎒"), tok("this pen", "A", "🖊️"), tok("this desk", "A", "🪑"),
           tok("that board", "B", "📋"), tok("that chair", "B", "🪑"), tok("that ruler", "B", "📏")]),
      [qa("What is this?", "It is a bag."),
       qa("What is that?", "That is a board."),
       qa("Is this your pen?", "Yes, it is."),
       qa("Is that a desk?", "Yes, it is.")]),

    L("Planet Gondax",
      [("pen", "🖊️"), ("pencil", "✏️"), ("book", "📕"), ("desk", "🪑"), ("chair", "🪑"), ("tablet", "📱")],
      "these vs those",
      ["These are pens.", "Those are desks.", "These are my books.", "Those are chairs.", "These are pencils."],
      [g("___ are pens. (here)", ["These", "Those"], "These", "🖊️"),
       g("___ are desks. (far)", ["Those", "These"], "Those", "🪑"),
       g("___ are my books. (here)", ["These", "Those"], "These", "📕")],
      [t("one pen -> many...?", "pen", ["pens", "penes", "pen"], "pens"),
       t("one desk -> many...?", "desk", ["desks", "deskes", "desk"], "desks"),
       t("one book -> many...?", "book", ["books", "bookes", "book"], "books")],
      [f("These are pens.", "These is pens.", "🖊️"),
       f("Those are desks.", "Those is desks.", "🪑"),
       f("These are my books.", "This are my books.", "📕")],
      srt("these (here)", "those (far)",
          [tok("these pens", "A", "🖊️"), tok("these books", "A", "📕"), tok("these tablets", "A", "📱"),
           tok("those desks", "B", "🪑"), tok("those chairs", "B", "🪑"), tok("those pencils", "B", "✏️")]),
      [qa("What are these?", "They are pens."),
       qa("What are those?", "Those are desks."),
       qa("Are these your books?", "Yes, they are."),
       qa("Are those chairs?", "Yes, they are.")]),

    L("Four Pointers",
      [("bag", "🎒"), ("board", "📋"), ("desk", "🪑"), ("chair", "🪑"), ("table", "🪑"), ("pencil", "✏️")],
      "this / that / these / those",
      ["This is a bag.", "That is a board.", "These are chairs.", "Those are desks.", "This is my pencil."],
      [g("___ is a bag. (one, here)", ["This", "These"], "This", "🎒"),
       g("___ are chairs. (many, here)", ["These", "This"], "These", "🪑"),
       g("___ is a board. (one, far)", ["That", "Those"], "That", "📋"),
       g("___ are desks. (many, far)", ["Those", "That"], "Those", "🪑")],
      [t("one bag -> many...?", "bag", ["bags", "bages", "bag"], "bags"),
       t("one chair -> many...?", "chair", ["chaires", "chairs", "chair"], "chairs"),
       t("one table -> many...?", "table", ["tables", "tablees", "table"], "tables")],
      [f("These are chairs.", "This are chairs.", "🪑"),
       f("That is a board.", "Those is a board.", "📋"),
       f("Those are desks.", "Those is desks.", "🪑")],
      srt("one", "many",
          [tok("this bag", "A", "🎒"), tok("that board", "A", "📋"), tok("this desk", "A", "🪑"),
           tok("these chairs", "B", "🪑"), tok("those desks", "B", "🪑"), tok("these tables", "B", "🪑")]),
      [qa("What is this?", "It is a bag."),
       qa("What are these?", "They are chairs."),
       qa("What is that?", "That is a board."),
       qa("What are those?", "Those are desks.")]),

    L("Robot Roll-call",
      [("box", "📦"), ("bus", "🚌"), ("dress", "👗"), ("glass", "🥛"), ("watch", "⌚"), ("brush", "🪥")],
      "plural -s / -es",
      ["These are boxes.", "These are buses.", "I have two watches.", "These are glasses.", "These are brushes."],
      [g("one box, two ___.", ["boxes", "boxs"], "boxes", "📦"),
       g("one bus, two ___.", ["buses", "buss"], "buses", "🚌"),
       g("one watch, two ___.", ["watches", "watchs"], "watches", "⌚")],
      [t("one box -> many...?", "box", ["boxs", "boxes", "box"], "boxes"),
       t("one dress -> many...?", "dress", ["dresses", "dresss", "dress"], "dresses"),
       t("one brush -> many...?", "brush", ["brushs", "brushes", "brush"], "brushes")],
      [f("These are boxes.", "These are boxs.", "📦"),
       f("These are buses.", "These are buss.", "🚌"),
       f("These are watches.", "These are watchs.", "⌚")],
      srt("add -s", "add -es",
          [tok("pen -> pens", "A", "🖊️"), tok("book -> books", "A", "📕"), tok("desk -> desks", "A", "🪑"),
           tok("box -> boxes", "B", "📦"), tok("bus -> buses", "B", "🚌"), tok("watch -> watches", "B", "⌚")]),
      [qa("How many boxes?", "Two boxes."),
       qa("Are these buses?", "Yes, they are."),
       qa("What are these?", "They are glasses."),
       qa("How do we spell more than one box?", "B-o-x-e-s.")]),

    L("Count the Bots",
      [("robot", "🤖"), ("box", "📦"), ("book", "📕"), ("pen", "🖊️"), ("bag", "🎒"), ("desk", "🪑")],
      "number + plural noun",
      ["I have one robot.", "I have two robots.", "I see three books.", "There are four pens.", "I have two boxes."],
      [g("I have two ___.", ["robots", "robot"], "robots", "🤖"),
       g("I have one ___.", ["robot", "robots"], "robot", "🤖"),
       g("I see three ___.", ["books", "book"], "books", "📕")],
      [t("one robot -> two...?", "robot", ["robots", "robotes", "robot"], "robots"),
       t("one box -> three...?", "box", ["boxs", "boxes", "box"], "boxes"),
       t("one pen -> four...?", "pen", ["pens", "penes", "pen"], "pens")],
      [f("I have two robots.", "I have two robot.", "🤖"),
       f("I see three books.", "I see three book.", "📕"),
       f("There are four pens.", "There are four pen.", "🖊️")],
      srt("one", "more than one",
          [tok("one robot", "A", "🤖"), tok("one book", "A", "📕"), tok("one pen", "A", "🖊️"),
           tok("two robots", "B", "🤖"), tok("three books", "B", "📕"), tok("four pens", "B", "🖊️")]),
      [qa("How many robots?", "Two robots."),
       qa("How many books do you see?", "Three books."),
       qa("Do you have one bag or two bags?", "Two bags."),
       qa("How many pens are there?", "Four pens.")]),

    L("Sound Lab: oo & oa",
      [("book", "📕"), ("moon", "🌙"), ("boat", "⛵"), ("coat", "🧥"), ("food", "🍽️"), ("room", "🚪")],
      "reading sounds: oo / oa",
      ["I read a book.", "I see the moon.", "This is a boat.", "That is my coat.", "I like the food."],
      [g("I read a ___.", ["book", "boat"], "book", "📕"),
       g("I see the ___ at night.", ["moon", "coat"], "moon", "🌙"),
       g("This is a ___ on the sea.", ["boat", "book"], "boat", "⛵")],
      [t("one book -> many...?", "book", ["books", "bookes", "book"], "books"),
       t("one boat -> many...?", "boat", ["boates", "boats", "boat"], "boats"),
       t("one coat -> many...?", "coat", ["coats", "coates", "coat"], "coats")],
      [f("This is a boat.", "This is a bot.", "⛵"),
       f("I see the moon.", "I see the mon.", "🌙"),
       f("I like the food.", "I like the fod.", "🍽️")],
      srt("oo sound", "oa sound",
          [tok("book", "A", "📕"), tok("moon", "A", "🌙"), tok("food", "A", "🍽️"),
           tok("boat", "B", "⛵"), tok("coat", "B", "🧥"), tok("road", "B", "🛣️")]),
      [qa("What do you read?", "I read a book."),
       qa("What do you see at night?", "I see the moon."),
       qa("What is on the sea?", "A boat."),
       qa("What is the first sound in 'boat'?", "The oa sound.")]),

    L("Classroom Champion",
      [("pen", "🖊️"), ("book", "📕"), ("apple", "🍎"), ("box", "📦"), ("desk", "🪑"), ("egg", "🥚")],
      "Unit 1 review",
      ["This is a pen.", "This is an apple.", "These are books.", "Those are desks.", "I have two boxes."],
      [g("This is ___ apple.", ["a", "an"], "an", "🍎"),
       g("___ are my books. (here)", ["These", "That"], "These", "📕"),
       g("one box, two ___.", ["boxes", "boxs"], "boxes", "📦"),
       g("___ is a pen. (far)", ["That", "These"], "That", "🖊️")],
      [t("one book -> many...?", "book", ["books", "bookes", "book"], "books"),
       t("one box -> many...?", "box", ["boxs", "boxes", "box"], "boxes"),
       t("one apple -> many...?", "apple", ["apples", "appls", "apple"], "apples")],
      [f("This is an apple.", "This is a apple.", "🍎"),
       f("These are books.", "These is books.", "📕"),
       f("I have two boxes.", "I have two boxs.", "📦")],
      srt("a", "an",
          [tok("pen", "A", "🖊️"), tok("book", "A", "📕"), tok("box", "A", "📦"),
           tok("apple", "B", "🍎"), tok("egg", "B", "🥚"), tok("orange", "B", "🍊")]),
      [qa("What is this?", "It is a pen."),
       qa("What are these?", "They are books."),
       qa("Is this an apple?", "Yes, it is."),
       qa("How many boxes?", "Two boxes.")]),
])


# Worlds 2-20 live in per-world files (w02.py .. w20.py) so each unit could be
# authored and reviewed on its own. They are assembled here in display order:
# index 100 = Level 101. Units 1-10 (Starters grammar) then the 10 advanced
# worlds (tenses, modals, conditionals, passive, reported speech, structure,
# quantifiers, polite/functional, everyday, big-idea vocabulary).
import w02, w03, w04, w05, w06, w07, w08, w09, w10
import w11, w12, w13, w14, w15, w16, w17, w18, w19, w20

WORLDS = [
    WORLD_01,
    w02.WORLD, w03.WORLD, w04.WORLD, w05.WORLD, w06.WORLD,
    w07.WORLD, w08.WORLD, w09.WORLD, w10.WORLD,
    w11.WORLD, w12.WORLD, w13.WORLD, w14.WORLD, w15.WORLD,
    w16.WORLD, w17.WORLD, w18.WORLD, w19.WORLD, w20.WORLD,
]
