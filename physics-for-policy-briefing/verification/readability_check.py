#!/usr/bin/env python3
"""Flesch-Kincaid readability check for the executive summary.

Verification metric (Project 15): Flesch-Kincaid Grade <= 14 for the executive
summary. This script computes the Flesch-Kincaid Grade Level and the Flesch
Reading Ease for the text in exec_summary.txt (the plain-text executive summary,
kept in sync with the LaTeX briefing).

No third-party dependencies: syllable counting uses a standard heuristic, so the
result is an estimate (typically within ~0.5 grade of textstat).

Usage:
    python3 verification/readability_check.py
"""
from __future__ import annotations

import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_TEXT = os.path.join(HERE, "exec_summary.txt")

VOWELS = "aeiouy"


def count_syllables(word: str) -> int:
    word = word.lower().strip(".,;:!?()[]\"'")
    if not word:
        return 0
    count = 0
    prev_vowel = False
    for ch in word:
        is_vowel = ch in VOWELS
        if is_vowel and not prev_vowel:
            count += 1
        prev_vowel = is_vowel
    # silent trailing 'e'
    if word.endswith("e") and count > 1:
        count -= 1
    return max(count, 1)


def analyse(text: str) -> dict:
    sentences = [s for s in re.split(r"[.!?]+", text) if s.strip()]
    words = re.findall(r"[A-Za-z']+", text)
    n_sentences = max(len(sentences), 1)
    n_words = max(len(words), 1)
    n_syllables = sum(count_syllables(w) for w in words)

    words_per_sentence = n_words / n_sentences
    syllables_per_word = n_syllables / n_words

    fk_grade = 0.39 * words_per_sentence + 11.8 * syllables_per_word - 15.59
    reading_ease = 206.835 - 1.015 * words_per_sentence - 84.6 * syllables_per_word

    return {
        "sentences": n_sentences,
        "words": n_words,
        "syllables": n_syllables,
        "words_per_sentence": words_per_sentence,
        "syllables_per_word": syllables_per_word,
        "fk_grade": fk_grade,
        "reading_ease": reading_ease,
    }


def main() -> int:
    path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_TEXT
    if not os.path.exists(path):
        print(f"ERROR: text file not found: {path}")
        return 2
    with open(path, encoding="utf-8") as fh:
        text = fh.read()

    r = analyse(text)
    print("=== Executive summary readability ===")
    print(f"  Words:               {r['words']}")
    print(f"  Sentences:           {r['sentences']}")
    print(f"  Words / sentence:    {r['words_per_sentence']:.2f}")
    print(f"  Syllables / word:    {r['syllables_per_word']:.2f}")
    print(f"  Flesch Reading Ease: {r['reading_ease']:.1f}")
    print(f"  Flesch-Kincaid Grade:{r['fk_grade']:.2f}")
    target = 14.0
    ok = r["fk_grade"] <= target
    print(f"\n  Target: FK Grade <= {target} -> {'PASS' if ok else 'FAIL'} "
          f"({r['fk_grade']:.2f})")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
