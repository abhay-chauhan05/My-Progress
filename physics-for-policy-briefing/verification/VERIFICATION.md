# Verification Metrics

Project 15 defines three verification metrics. This document records how each is
met and how to reproduce the result.

## 1. Source quality — target: >= 15 peer-reviewed / official sources

**Result: 20 sources** (see [`../references.bib`](../references.bib)).

Breakdown by class:

- Official / government: 10 (NRC SECY vote, NRC Federal Register notice 2023,
  NRC proposed rule 2026, 10 CFR Part 30, UK fusion-regulation factsheet, UK
  fusion strategy 2023, UK Environment Agency decision, Agile Nations joint
  statement, UK draft NPS EN-8, CRS report R48866).
- IAEA: 4 (first technical meeting on fusion safety/regulation, fusion safety
  status report, TECDOC-2049 on the D-T fuel cycle, tritium-release model
  harmonisation).
- Peer-reviewed: 5 (Phil. Trans. R. Soc. A proportionate-safety paper; ANS
  Fusion Science & Technology ITER safety basis; ANS Safety-in-Design
  methodology; Springer Journal of Fusion Energy radwaste recycling; Springer
  Journal of Fusion Energy tritium breeding).
- Legal/industry analysis: 1 (Orrick analysis of the 2026 proposed rule).

To count entries:

```bash
grep -cE '^@' references.bib   # -> 20
```

## 2. Policy options — target: >= 3 distinct, quantitatively appraised

**Result: 4 distinct options, scored via weighted MCDA.**

Reproduce the scoring and sensitivity check:

```bash
python3 verification/mcda_score.py
```

Expected output (weighted totals out of 100):

```
C: Adaptive (recommended)       7.90
D: Harmonisation-first          6.40
B: Light byproduct              6.05
A: Fission-equivalent           5.20
Option C remains top in every tested scenario.
```

## 3. Readability — target: Flesch-Kincaid grade <= 14 for executive summary

**Result: PASS.** Built-in heuristic reports FK grade ~5.7; cross-checked against
the `textstat` library at ~6.0. Both are comfortably under the 14 threshold.

Reproduce:

```bash
python3 verification/readability_check.py
# Optional cross-check:
pip install textstat -q && python3 -c "import textstat,sys; print(textstat.flesch_kincaid_grade(open('verification/exec_summary.txt').read()))"
```

The executive summary text lives in
[`exec_summary.txt`](exec_summary.txt) and is kept in sync with the LaTeX
briefing's Section 1.

## Briefing document

The 10-page briefing builds cleanly with no LaTeX errors and no undefined
citations:

```bash
cd briefing
pdflatex -interaction=nonstopmode briefing.tex
bibtex briefing
pdflatex -interaction=nonstopmode briefing.tex
pdflatex -interaction=nonstopmode briefing.tex
```
