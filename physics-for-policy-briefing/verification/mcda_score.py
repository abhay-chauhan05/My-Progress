#!/usr/bin/env python3
"""Reproducible MCDA scoring for the fusion-regulation policy option appraisal.

Regenerates the weighted-score table in deliverables/04-policy-option-appraisal.md
and runs a simple +/- 5 weight sensitivity check.

Usage:
    python3 verification/mcda_score.py
"""
from __future__ import annotations

import itertools

# Criterion -> weight (must sum to 100)
WEIGHTS = {
    "Safety": 30,
    "Proportionality": 20,
    "Innovation/speed": 15,
    "Adaptability": 15,
    "Public trust": 10,
    "Intl coherence": 10,
}

# Option -> {criterion: score 0..10}
SCORES = {
    "A: Fission-equivalent": {
        "Safety": 9, "Proportionality": 2, "Innovation/speed": 2,
        "Adaptability": 4, "Public trust": 7, "Intl coherence": 5,
    },
    "B: Light byproduct": {
        "Safety": 5, "Proportionality": 9, "Innovation/speed": 9,
        "Adaptability": 4, "Public trust": 4, "Intl coherence": 4,
    },
    "C: Adaptive (recommended)": {
        "Safety": 8, "Proportionality": 8, "Innovation/speed": 7,
        "Adaptability": 9, "Public trust": 8, "Intl coherence": 7,
    },
    "D: Harmonisation-first": {
        "Safety": 7, "Proportionality": 6, "Innovation/speed": 4,
        "Adaptability": 6, "Public trust": 7, "Intl coherence": 9,
    },
}


def weighted_total(scores: dict[str, int], weights: dict[str, int]) -> float:
    return sum(weights[c] * scores[c] for c in weights) / 100.0


def main() -> None:
    assert sum(WEIGHTS.values()) == 100, "weights must sum to 100"

    print("=== Baseline MCDA (weighted total out of 100) ===")
    results = {opt: weighted_total(s, WEIGHTS) for opt, s in SCORES.items()}
    for opt, total in sorted(results.items(), key=lambda kv: kv[1], reverse=True):
        print(f"  {opt:30s} {total:5.2f}")
    winner = max(results, key=results.get)
    print(f"  -> Top option: {winner}\n")

    # Sensitivity: swing each weight by +/-5 (rebalancing the rest proportionally)
    print("=== Sensitivity check (+/-5 on each weight) ===")
    crits = list(WEIGHTS)
    still_top = True
    for crit, delta in itertools.product(crits, (-5, +5)):
        w = dict(WEIGHTS)
        w[crit] += delta
        # rebalance: distribute -delta across the other criteria proportionally
        others = [c for c in crits if c != crit]
        share = -delta / len(others)
        for c in others:
            w[c] += share
        res = {opt: weighted_total(s, w) for opt, s in SCORES.items()}
        top = max(res, key=res.get)
        if top != winner:
            still_top = False
            print(f"  weight {crit} {delta:+d} -> top changes to {top}")
    if still_top:
        print("  Option C remains top in every tested scenario.")


if __name__ == "__main__":
    main()
