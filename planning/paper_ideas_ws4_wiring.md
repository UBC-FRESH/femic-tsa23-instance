# Two papers, mined for what ws4 can use now

Both were read via Crossref/OpenAlex because the publisher pages return 403; the method
sections were therefore not available, so the proposals below are grounded in the abstracts
and in what this workspace already implements.

## Paper 1 — Bhusal et al. (2026), *Forests* 17(8):886

**Landscape-Level Optimization of Silvicultural Treatments for Wildfire Risk Reduction:
Comparative Applications in Portugal and Greece.**

- Spatially explicit **ILP** for fuel-treatment allocation under operational constraints.
- Two risk representations: a stand-level **wildfire resistance indicator** that accounts for
  the spatial influence of neighbouring stands (Portugal), and **simulation-derived spread
  probabilities from FSim** used to prioritise high-risk zones (Greece).
- Results: resistance 0.9907 → 0.9959; expected risk 0.1751 → 0.1701, across increasing
  treatment-area scenarios. **Modest but consistent.**
- The claim is transferability of the framework across data-poor and data-rich contexts.

### What maps onto ws4

| paper element | ws4 today | gap |
| --- | --- | --- |
| ILP allocation | `opt/mip.py` + `opt/exact.py` (per-block option choice, subset of blocks) | exact lane excludes spread connectivity; no spatial objective |
| resistance indicator (neighbour influence) | `spread/accounts.py` (compartment, fragmentation) | measures fragmentation, not a neighbourhood hazard index |
| FSim spread probabilities | **nothing** — but the instance's spread model already computes per-block burn probability | not exported as a feature |
| treatment-area scenarios | the density sweeps (E9/E10) | done |

## Paper 2 — Jones et al. (2026), *Environmental Reviews* 10.1139/er-2025-0281

**The changing landscape of fire fuels in western Canada: insights from 40 years of public
data and research.**

- Systematic review of **245 articles**, 1985–2025, across BC, AB, SK, NWT, YT.
- Plus analysis of **National Burned Area Composite** data: large fires (≥95th percentile),
  pre-fire vegetation types, post-fire severity trends.
- Findings: fuels are shifting in abundance, composition and condition; **extremely large
  fires (P95) have increased over the last decade**; **increasing severity does not
  necessarily mean increasing size**; geographic gaps (northern regions); current systems
  represent ongoing fuel change poorly.
- Explicitly names a limitation: **"structural arrangement and continuity of fuels"** is
  under-studied.

That last point is a positioning gift: the bridge work (E2e–E16) is a measurement of exactly
arrangement and continuity, and the compartment account is a continuity metric.

## What I would wire, in order

### A. Risk-weighted hazard — built, needs a decision (paper 1, Greece)

`scripts/add_burn_probability_feature.py` adds two targetable features to a compiled dataset:

- `feature.BurnProbability` — the block's burn probability under an untreated landscape;
- `feature.RiskWeightedHazard` — the track's hazard curve scaled by that probability, so a
  treatment scores by how much it lowers hazard *where fire is likely*.

Built from the instance's own spread model (`run_matched_footprint.py` with an empty mask):
102,128 blocks, 92,226 with `p > 0`, 27 distinct probability curves, 321,449 feature rows.
Verified: a simulate reports `feature.BurnProbability` = 12.19M and
`feature.RiskWeightedHazard` = 12.31M at offset 0, falling as stands age.

**Decision needed before it is used for targets:** the probability is from one wind
direction (225°), 200 ignitions, no treatment, p90 weather. For a paper-grade risk map it
should be averaged over the weather ladder (E10's ten scenarios) — the same one-wind caveat
applies as everywhere else in the model.

### B. Severity account — immediate, no new data (paper 2, severity ≠ size)

`runtime/fire/fbp_stand_curves.csv` already carries `cfb` (crown fraction burned) per AU,
scenario, state and age. A `feature.CrownFractionBurned` per track gives the model a second
outcome axis, which the review says the literature conflates with area. Cost: one script
like the hazard builder; no new inputs.

### C. Neighbourhood resistance account — medium (paper 1, Portugal)

A spatial account `resistance.<sub>`: for each block, `1 −` the hazard-weighted mean of its
topological neighbours (or a distance-weighted ring). That is the paper's indicator and it
targets the review's "arrangement and continuity" gap directly. Implementation is a sibling
of `ws4/spread/accounts.py`; the topology and the hazard feature both exist.

### D. ILP versus the heuristic on the hazard target — cheap, and tells the truth

Run `opt/exact.py` on a 500-block subset with the hazard target and compare its penalty with
the seeded SA result (E21: 985,981.3). The paper's method is ILP; ws4's exact lane stops at
additive accounts, so this would quantify the price of the spatial features the ILP cannot
see. Worth doing before claiming the heuristic is good enough.

### E. NBAC validation overlay — validation, not wiring (paper 2)

The review's large-fire analysis rests on the National Burned Area Composite. Overlaying
NBAC polygons on the modelled burn probability would be the first external check of this
model's spatial risk surface. Medium effort: fetch NBAC, rasterise/aggregate to blocks,
compare. It does not make the model better; it makes its claims testable.

## What not to copy

Both papers report **small** effects: a 0.5% resistance gain, a 0.3% risk reduction. Our own
feasible hazard result is ~0.6% at $100M (E21). That consistency is worth stating in the
thesis, and it is a reason not to oversell a spatial objective as transformative.

## Incidental, and blocking: ws4's schedule schema changed

The pull to `0075da9` rejects the `period` column; schedules are keyed by `offset` (offset 0
is the first simulation year). Handled here:

- writers updated: `bridge_matched_footprint.py`, `greedy_hazard_schedule.py`,
  `ws4_bridge_test.py`;
- 58 stored schedule CSVs migrated (`period` → `offset`, values unchanged; our treatments
  were always first-year);
- verified: `ft_cap.csv` runs again and returns 9,983.36 ha / $199.67M.

Any command in `planning/bridge_experiment_log.md` that hands ws4 a schedule now needs the
same treatment if the CSV predates this change.
