# -*- coding: utf-8 -*-
"""Authoring helpers for the hand-written grammar levels (see grammar_content.py
and the per-world files w02..w20). Correct answers are given as STRINGS so a
typo can never silently select the wrong option; the helpers look up the index
and assert the answer is one of the options."""


def g(text, options, answer, emoji=""):
    assert "___" in text, "gap needs a blank: %r" % text
    assert answer in options, "gap answer %r not in %r" % (answer, options)
    assert 2 <= len(options) <= 4, "gap needs 2-4 options: %r" % options
    assert len(set(options)) == len(options), "gap has duplicate options: %r" % options
    return {"text": text, "options": list(options), "correct": options.index(answer), "emoji": emoji}


def t(prompt, base, options, answer):
    assert answer in options, "transform answer %r not in %r" % (answer, options)
    assert len(options) == 3, "transform needs 3 options: %r" % options
    assert len(set(options)) == len(options), "transform has duplicate options: %r" % options
    return {"prompt": prompt, "base": base, "options": list(options), "correct": options.index(answer)}


def f(right, wrong, emoji=""):
    assert right != wrong, "fix right/wrong identical: %r" % right
    return {"right": right, "wrong": wrong, "emoji": emoji}


def tok(text, cat, emoji=""):
    assert cat in ("A", "B"), "token cat must be A/B: %r" % cat
    return {"t": text, "cat": cat, "emoji": emoji}


def srt(binA, binB, tokens):
    a = [x for x in tokens if x["cat"] == "A"]
    b = [x for x in tokens if x["cat"] == "B"]
    assert len(a) >= 2 and len(b) >= 2, "sort needs >=2 per bin (%d/%d)" % (len(a), len(b))
    return {"binA": binA, "binB": binB, "tokens": list(tokens)}


def qa(q, a):
    return {"q": q, "a": a}


def L(name, items, target, sentences, gap, transform, fix, sort, pairs):
    assert len(items) >= 6, "%s: need >=6 items" % name
    assert len(sentences) >= 4, "%s: need >=4 sentences" % name
    assert len(gap) >= 3, "%s: need >=3 gap" % name
    assert len(transform) >= 3, "%s: need >=3 transform" % name
    assert len(fix) >= 3, "%s: need >=3 fix" % name
    assert len(pairs) >= 3, "%s: need >=3 pairs" % name
    return {
        "name": name, "items": items, "target": target, "sentences": sentences,
        "gap": gap, "transform": transform, "fix": fix, "sort": sort, "pairs": pairs,
    }


def W(world, sub, levels):
    assert len(levels) == 10, "%s: expected 10 levels, got %d" % (world, len(levels))
    return {"world": world, "sub": sub, "levels": levels}
