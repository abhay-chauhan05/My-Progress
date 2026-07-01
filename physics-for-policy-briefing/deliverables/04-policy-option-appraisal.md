# Deliverable 4 — Policy Option Appraisal

Four distinct policy options are appraised against weighted criteria using a
**Multi-Criteria Decision Analysis (MCDA)** — satisfying the brief's requirement
for **>= 3 distinct, quantitatively appraised** options. Each option also carries
a qualitative pros / cons / second-order-effects assessment.

The scoring is reproducible: run
[`../verification/mcda_score.py`](../verification/mcda_score.py) to regenerate the
table below.

## The four options

| Option | One-line description |
|--------|----------------------|
| **A — Full fission-equivalent licensing** | Regulate fusion plants under the existing nuclear *reactor / site licence* regime (NRC Part 50/52; UK ONR nuclear site licence). |
| **B — Light byproduct-only regime** | Regulate only the radioactive materials (tritium, activation products) with minimal facility-level oversight (pure 10 CFR Part 30 / general health-and-safety). |
| **C — Proportionate, adaptive, review-gated framework** | Hazard-based fusion-specific regime (byproduct + environmental + worker safety) with mandatory periodic review tied to maturing tritium/activation data and international harmonisation. |
| **D — International-harmonisation-first** | Defer a settled national regime until an IAEA-led common framework exists; interim case-by-case licensing. |

Options A and B are the real-world "poles"; C is the adaptive middle path; D
prioritises global coherence. The status quo in both the US and UK is closest to
a **fixed** version of B/C; Option C adds the adaptive review mechanism the risk
register calls for.

## MCDA criteria and weights

Weights reflect a policymaker's priorities for a low-hazard but high-profile
emerging technology. They sum to 100.

| Criterion | Weight | Rationale |
|-----------|-------:|-----------|
| Public & environmental safety | 30 | Non-negotiable floor; tritium and waste must be controlled [iaeatritiumharmonization]. |
| Proportionality to actual hazard | 20 | Avoid fission-scale burden on a non-fission hazard [ukfusionregfactsheet]. |
| Innovation / time-to-deploy | 15 | Near-term commercialisation at stake [crs2026fusion]. |
| Adaptability to new evidence | 15 | Key parameters are unknown, not just contested [tritiumbreeding2018]. |
| Public trust & legitimacy | 10 | Fusion-fission conflation risk [proportionate2024]. |
| International coherence | 10 | Global developers; arbitrage risk [agilenations2023]. |

## Scores (0-10 per criterion; weighted total out of 100)

| Criterion (weight) | A: Fission-equiv | B: Light byproduct | C: Adaptive | D: Harmonisation-first |
|---|---:|---:|---:|---:|
| Safety (30) | 9 | 5 | 8 | 7 |
| Proportionality (20) | 2 | 9 | 8 | 6 |
| Innovation / speed (15) | 2 | 9 | 7 | 4 |
| Adaptability (15) | 4 | 4 | 9 | 6 |
| Public trust (10) | 7 | 4 | 8 | 7 |
| Int'l coherence (10) | 5 | 4 | 7 | 9 |
| **Weighted total /100** | **5.20** | **6.05** | **7.90** | **6.40** |

> Weighted total = sum(weight x score) / 100. See script for exact arithmetic.

**Ranking: C (7.90) > D (6.40) > B (6.05) > A (5.20).**

The result is robust to reasonable weight changes: in a sensitivity check that
swings each weight +/- 5 points, Option C remains top in every scenario tested
(see script output).

---

## Qualitative appraisal

### Option A — Full fission-equivalent licensing

- **Pros:** Maximum safety assurance; reuses mature institutions and public familiarity.
- **Cons:** Disproportionate to a hazard with no chain-reaction or high-level-waste risk [ukfusionregfactsheet]; slow and costly; likely to push developers to lighter-touch jurisdictions.
- **Second-order effects:** Could entrench the misleading "fusion = fission" framing; risks ceding industrial leadership; ties up scarce nuclear-regulator capacity.

### Option B — Light byproduct-only regime

- **Pros:** Fast, cheap, attractive to investment; well matched to the dominant tritium/activation hazard model [nrc2026proposedrule].
- **Cons:** Thin facility-level oversight; weak hooks for large activated-waste volumes and emergency planning; vulnerable to a confidence shock if an unmodelled hazard appears [iaeatritiumharmonization].
- **Second-order effects:** A single incident could trigger reactive over-correction toward Option A; limited public reassurance.

### Option C — Proportionate, adaptive, review-gated framework (RECOMMENDED)

- **Pros:** Keeps the proportionate byproduct core but adds environmental discharge control, worker safety, waste-route authorisation (including recycling/clearance [radwasterecycling2023]), and **mandatory periodic review** triggered by new activation/tritium data and IAEA harmonisation milestones. Scores highest on safety-adjusted proportionality and on adaptability.
- **Cons:** More design and review effort than B; requires sustained regulator capability investment [ukenvagency2022], [sidmethodology2026].
- **Second-order effects:** Builds durable public trust; positions the jurisdiction to lead IAEA harmonisation rather than follow; reduces lock-in risk (R5).

### Option D — International-harmonisation-first

- **Pros:** Best long-run global coherence; avoids early divergence and arbitrage [agilenations2023], [iaea2023meeting].
- **Cons:** IAEA fusion standards are nascent and non-binding [iaeafusionsafety]; waiting forfeits near-term certainty and may delay deployment past developers' early-2030s targets [crs2026fusion].
- **Second-order effects:** Cedes first-mover regulatory influence; interim case-by-case licensing creates its own unpredictability.

---

## Recommendation

Adopt **Option C**. It preserves the proportionate, fission-distinct stance that
both the US and UK have already chosen [nrc2023vote], [ukfusionregfactsheet],
while explicitly engineering in the **adaptability** the evidence demands given
genuinely unknown activation inventories and commercialisation timelines
[tritiumbreeding2018], [crs2026fusion]. Crucially, Option C is **not a rejection
of the status quo** but an upgrade to it: keep the byproduct-material core, add
environmental/worker-safety and waste-clearance provisions, and bind the regime
to scheduled review gates aligned with IAEA harmonisation [iaea2023meeting].
