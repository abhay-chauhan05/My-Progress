# Physics-for-Policy Regulatory Briefing (Project 15)

**Policy question:** How should regulators structure the licensing and oversight
regime for **commercial nuclear fusion energy facilities**, given that fusion's
hazard profile differs fundamentally from fission?

This repository delivers a complete, evidenced regulatory briefing aimed at a
non-physicist policymaker (e.g. a legislative committee staffer, an energy
ministry official, or a regulator's strategy lead). It follows the structure of
the **UK Government Analysis Function** policy-analysis standards and the **RAND**
briefing format.

## Why this topic

Fusion has moved from a perpetual "30 years away" laboratory pursuit to a
near-term commercial prospect. Private firms target grid connection in the early
2030s, and regulators on both sides of the Atlantic have, since 2022-2026, made
binding decisions about *how* to license fusion. The US Nuclear Regulatory
Commission (NRC) and the UK Government chose markedly different legal routes to
the same conclusion — that fusion should **not** be regulated like fission. That
divergence, the live US rulemaking (proposed rule published February 2026), and
the international harmonisation effort led by the IAEA make this a genuinely
current, contested, physics-adjacent regulatory question.

## Deliverables

| # | Deliverable | File |
|---|-------------|------|
| 1 | Stakeholder map | [`deliverables/01-stakeholder-map.md`](deliverables/01-stakeholder-map.md) |
| 2 | Evidence synthesis (>=15 sources) | [`deliverables/02-evidence-synthesis.md`](deliverables/02-evidence-synthesis.md) |
| 3 | Risk & uncertainty register | [`deliverables/03-risk-uncertainty-register.md`](deliverables/03-risk-uncertainty-register.md) |
| 4 | Policy option appraisal (>=3 options) | [`deliverables/04-policy-option-appraisal.md`](deliverables/04-policy-option-appraisal.md) |
| 5 | 10-page briefing document | [`briefing/briefing.tex`](briefing/briefing.tex) |

Supporting material:

- [`references.bib`](references.bib) — Zotero-exportable BibTeX, 20 cited sources.
- [`verification/`](verification/) — readability and metric checks.

## Verification metrics (target -> result)

| Metric | Target | Result |
|--------|--------|--------|
| Source quality | >= 15 peer-reviewed / official sources | **20** (see `references.bib`) |
| Policy options | >= 3 distinct, quantitatively appraised | **4** (weighted MCDA scoring) |
| Readability (exec summary) | Flesch-Kincaid grade <= 14 | see `verification/VERIFICATION.md` |

## Building the briefing PDF

```bash
cd briefing
latexmk -pdf briefing.tex      # or: pdflatex briefing.tex (x2) && bibtex briefing
```

## Running the readability check

```bash
python3 verification/readability_check.py
```

## A note on scope and honesty

This is a student-level policy briefing, not an official regulatory document.
Every factual claim is tied to a numbered source in `references.bib`. Where the
evidence is contested or unknown, the briefing says so explicitly (see the risk
and uncertainty register). Figures attributed to a single secondary source are
flagged as such.
