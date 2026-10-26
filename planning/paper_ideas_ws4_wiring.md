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

#### The map check that made it necessary

`scripts/check_treated_map.py` compares a schedule's treated blocks with the landscape.
Run on the unweighted greedy schedule it exposed a defect **in the greedy, not the data**:

| | treated | landscape | ratio |
| --- | ---: | ---: | ---: |
| hazard | 1.0434 | 1.2493 | 0.84 |
| burn probability | 0.0286 | 0.0323 | 0.89 |
| area (ha) | 10.33 | 9.68 | 1.07 |
| share in top burn-probability quintile | 17.7% | 23.2% | 0.76x |
| connected components | 2,428 | — | — |
| largest component | 315 ha (1%) | — | — |

The treatments were **thinner than the landscape** in high-risk area and scattered into 2,428
pieces. The cause: every fuel-break candidate ties on cost per hazard-hectare
(5,000 / 0.95, area cancels), so the sort was a coin toss resolved by block id. There are
66,584 eligible blocks and the ranking distinguished none of them.

With `--burn-probability` the ranking becomes `cost / (reduction x p)`:

| | unweighted | risk-weighted |
| --- | ---: | ---: |
| blocks | 2,969 | 4,620 |
| mean burn probability | 0.0286 (0.89x) | **0.0773 (2.39x)** |
| in top risk quintile | 17.7% (0.76x) | **99.4% (4.29x)** |
| components | 2,428 | **535** |
| largest component | 315 ha (1%) | **15,737 ha (56%)** |
| hazard reduction | 20,856 | 19,751 |

So the risk weighting does not just change a number; it turns an arbitrary scatter into a
concentrated high-risk strategy — which is the FSim idea doing real work. The cost is a
slightly smaller hazard reduction (19,751 against 20,856) because the ranking now prefers
small, risky blocks over large, safe ones.

That also explains why the unweighted frontier (idea F) is only a shape: its selection was
arbitrary within each budget.

#### Weather averaging softens it

`scripts/burn_probability_map.py` runs every scenario in the ladder (ten, from median to
extreme) with **no treatment** — the earlier map let thinned states carry a 0.6x rate, so it
was not a clean baseline — and averages the per-block probability.

| variant | blocks | mean p (ratio to landscape) | top risk quintile | components | largest | hazard reduction |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| unweighted | 2,969 | 0.0286 (0.89x) | 17.7% | 2,428 | 315 ha | 20,856 |
| one scenario (p90) | 4,620 | 0.0773 (2.39x) | 99.4% | 535 | 15,737 ha | 19,751 |
| weather-averaged | 5,741 | 0.0481 (**1.94x**) | 90.7% | 744 | 7,723 ha | 19,966 |

So the strategy survives: still about twice the landscape's burn probability, still 90% of
the treated area in the top risk quintile, still a 7,723 ha connected component. But the
single-storm version overstated it — 99.4% in the top quintile was partly the schedule being
fitted to one storm's geography.

Two cautions on reading the table:

- The "top quintile" is defined against the same map used for weighting, so a high share is
  partly by construction. The informative comparison is **across variants**, not the absolute
  multiple.
- The averaged map is still one wind direction; averaging weather does not average wind.

### B. Severity account — built (paper 2, severity ≠ size)

`scripts/add_cfb_feature.py` adds `feature.CrownFractionBurned` from the FBP curves already
in the workspace. Verified: **258,825 tracks covered, 0 missing, 87 distinct (AU, state)
curves**; a simulate reports 934,420 crown-burn-hectares at offset 0 under p90 weather
(a mean CFB of about 0.945 over 988,816 ha).

That gives the model the second outcome axis the review says the literature conflates with
area: two landscapes can burn the same area at very different severity, and now the model
can say so.

Two recorded simplifications:

- FBP carries only `untreated` and `thinned`; a state containing `_ft` maps to thinned and
  everything else to untreated, so fuel-break and surface-fuel states read as untreated
  (conservative for severity).
- The curve is extended past the last modelled age with its final value, so a stand at age
  255 does not silently fall back to age-0 severity.

### C. Neighbourhood resistance account — prototyped, and it does not rank (paper 1, Portugal)

`scripts/resistance_metric.py` computes the paper's indicator against the real simulator:

```
h_i        = feature.FuelHazard at the block
s_i        = (h_i + sum_j h_j) / (1 + degree_i)
resistance = 1 - s_i
```

Run on the three bridge patterns (5-year replay, area-weighted):

| pattern | resistance (offset 4) | hazard |
| --- | ---: | ---: |
| barrier | 0.00687 | 0.99589 |
| clumped | **0.00781** | 0.99472 |
| random | 0.00654 | 0.99616 |

The ranking is **clumped > barrier > random**, which is *not* the fire ranking
(barrier < clumped < random). It is identical at 50 m and 100 m search distances, so this is
not a neighbourhood-size artefact.

**Why it fails:** with equal neighbour weights the indicator is essentially `1 − mean
neighbourhood hazard`, so it inherits the hazard account's ordering — and the hazard account
is not a fire-response proxy (E7/P16.1). The paper's gains were 0.9907 → 0.9959; the same
near-no-op magnitude.

Conclusion: **do not promote this to ws4 as a fire-response objective.** It can be reported
as a proximity/adaptation metric with the same caveat as the compartment account, or dropped.
A version that could rank would need a directional, rate-aware treatment of spread — i.e. the
fire model, not an index.

### D. ILP versus the heuristic — attempted, and the exact lane does not scale

`ws4 solve-mip --limit-blocks N` is the exact lane. On this instance:

| subset | wall clock | result |
| ---: | ---: | --- |
| 50 blocks | **300 s timeout** | no output |
| 300 blocks | 1200 s timeout | no output |

It enumerates options per block and simulates each option on its own, which is far too slow
even for a diagnostic subset of this dataset. So a like-for-like ILP-versus-SA comparison is
**not available here**; the paper's ILP method would need block aggregation (development
types) before it can be applied at this scale — which is exactly the trade-off the paper
does not discuss.

Recorded as a blocker, not a result: it needs a subset of a *small* dataset, not a subset of
a 102k-block landscape.

### E. NBAC validation overlay — validation, not wiring (paper 2)

The review's large-fire analysis rests on the National Burned Area Composite. Overlaying
NBAC polygons on the modelled burn probability would be the first external check of this
model's spatial risk surface. Medium effort: fetch NBAC, rasterise/aggregate to blocks,
compare. It does not make the model better; it makes its claims testable.

## Paper 3 — Ulloa-Fierro et al. (2026), *Ecological Informatics* 99:104044

**Treemün: a Python framework for spatial growth-and-yield simulation and harvest scheduling
optimization in plantation forests** (open source, MIT, PyPI `treemun-sim`, repo
`fulloaf/treemun`).

- Discrete-time growth-and-yield simulator + **MILP** (Pyomo; HiGHS/CBC/CPLEX), for
  *Pinus radiata* and *Eucalyptus globulus* plantations.
- **Spatial adjacency and green-up constraints**, hard and soft, with shared-boundary
  weights; GeoPackage in/out.
- **Carbon accounting** on a dry-wood basis, and a carbon-stock-time objective.
- **Multi-objective search**: NPV vs carbon weighted fronts, Pareto and epsilon-constraint
  generation with knee-point detection.
- Reports 44 passing tests and reproducible benchmark notebooks.

### What maps onto ws4

| paper element | ws4 today | gap |
| --- | --- | --- |
| MILP assignment | `opt/mip.py`, `opt/exact.py` (subset, additive accounts) | exact lane excludes spread connectivity |
| adjacency / green-up | `opt/spatial.py` (opening, green-up, core area; move-based) | comparable; ws4 may even be ahead on incremental evaluation |
| carbon accounting | not present | ws4 has no carbon account |
| **multi-objective front generation** | weighted targets only | **no Pareto / epsilon-constraint driver** |
| GeoPackage export of the schedule | web map, no GIS export | no schedule → GPKG writer |

### F. Cost-hazard frontier — built (paper 3's epsilon-constraint idea)

`greedy_hazard_schedule.py --budgets` now traces the frontier by cutting the same
cost-per-hazard ranking at several budgets:

| budget | blocks | hazard reduction | projected hazard at year 4 |
| ---: | ---: | ---: | ---: |
| $20M | 488 | 5,656 | 986,678 |
| $40M | 1,089 | 9,456 | 982,878 |
| $60M | 1,744 | 13,256 | 979,078 |
| $80M | 2,364 | 17,056 | 975,278 |
| $100M | 2,969 | 20,856 | 971,478 |
| $120M | 3,589 | 24,656 | 967,678 |
| $150M | 4,424 | 30,356 | 961,978 |
| $200M | 5,940 | 39,856 | 952,478 |

Caveat: these are greedy projections. The simulated $100M point was 973,334, about 1,856
higher than projected, because per-block reductions are not additive. The frontier is a
shape, not a set of quotes; the points the thesis uses should be simulated.

That frontier is the cost-benefit curve the thesis needs, and it immediately explains the
seeded optimizer's 986,000: the slightly-better-than-expected result sits near the $20M end
of the curve, which is worth checking against its actual spend.

### G. Carbon account — medium (paper 3)

ws4 has no carbon account. A `product.Carbon` from harvested/standing biomass would make the
NPV-versus-carbon question askable here as it is in Treemün. Needs a biomass-to-carbon
conversion (species-specific density and fraction), which our TIPSY output already implies
but does not expose.

### H. Schedule → GeoPackage export — built (paper 3)

`scripts/schedule_to_geopackage.py` joins a schedule to the dissolved block geometry:

- **102,128 features**, EPSG:3005, one per block, 120 MB;
- columns `block_id`, `area_ha`, `treatment`, `offset`, `treated`, `geometry`;
- optional `--dataset` adds the block's `feature.FuelHazard`;
- verified on the greedy schedule: 2,969 treated blocks, all FB.

The web service (`docs/reference/web.rst`) already joins runs to geometry for the browser map
via `GET /api/runs/{run}/map`, with `bbox` and `zoom`; this is the static counterpart for
QGIS, and it needs no server.

## The risk-weighted objective as a ws4 target

`compiled_sf_risk` carries the wind-and-weather-averaged `feature.BurnProbability` and the
derived `feature.RiskWeightedHazard`; `config/risk_objective.yaml` targets the latter with the
same $100M split used for the plain hazard objective.

| | plain hazard (E21) | risk-weighted |
| --- | ---: | ---: |
| baseline, year 4 | 992,334 | 9,419,209 |
| target | 986,000 | 9,346,000 |
| reached | **985,981** | **9,415,185** |
| gap closed | met | **5.5%** |
| blocks | — | 199 (82 CC, 77 FB, 26 FT, 14 SF) |
| spend | — | $6.4M of $100M |

So the account is **targetable** — ws4 accepts it and evaluates it per period — but the
optimizer closes 5.5% of the required gap. The greedy closes all of it and would go further:
5,741 fuel-break blocks, 19,966 hazard-ha, roughly **50x** the optimizer's movement on this
objective.

**The detail that matters more than the shortfall:** the schedule includes **82 clearcuts**.
A plain CC is the model's harvest treatment and it creates the `cc_pl` slash state (hazard
2.0), so every CC pushes the objective the wrong way while the 77 fuel breaks push it right.
The optimizer is fighting itself, and the seed does not know that harvesting is a cost under
this objective.

That is a modelling problem before it is an optimizer problem: **a hazard objective must
price or exclude the harvest treatment**, or pair CC with its abatement (which is exactly
what FB is — clearcut plus disposal). Otherwise the model will "reduce risk" by harvesting
and then undo it.

#### The controlled test: CC removed from the decision set

Same dataset, same target, CC rows removed from `treatments` so the optimizer can only treat:

| | with CC available | CC removed |
| --- | ---: | ---: |
| result, year 4 | 9,415,185 | **9,410,000** |
| gap closed (target 9,346,000, baseline 9,419,209) | 5.5% | **12.6%** |
| blocks | 199 (82 CC) | 195 (159 FB, 26 FT, 10 SF) |
| spend | $6.4M of $100M | $12.2M of $100M |

Removing CC **doubled** the progress, which confirms it was working against the objective.
But the optimizer still uses **12% of the budget** and schedules 195 blocks, and still closes
only an eighth of the target — so the binding constraint is the search scale (ws4#165), not
CC and not the budget.

So the two problems are separable and both real:

1. **Modelling**: a hazard objective that lets the model harvest will fight itself. Fix by
   pricing CC or removing it from the option set.
2. **Search**: even with the right options, the seeded optimizer reaches 195 blocks where the
   greedy reaches 5,741.

##### The CC-slash sensitivity

`complete_hazard_feature.py --cc-slash H` varies the parameter; the greedy re-ranks:

| CC slash | baseline hazard, year 4 | greedy reduction at $100M | share of baseline |
| ---: | ---: | ---: | ---: |
| 1.5 | 992,527 | 19,928 | 2.01% |
| 2.0 | 996,237 | 20,856 | 2.09% |
| 3.0 | 1,003,658 | 22,345 | 2.23% |

The baseline moves ~1% across a 2x range, but the **achievable reduction moves 12%** — and
the reason is mechanics, not noise: 15,179 fuel-break options sit on tracks that are
themselves in the `cc_pl` slash state (plantations past 90 years), so a higher assumed slash
hazard makes those blocks more valuable to treat. The decision (fuel breaks only) does not
change; the effect size does, modestly.

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


## Withdrawn: the risk-weighted optimizer results

**Both optimizer runs on `feature.RiskWeightedHazard` are withdrawn**, including the one that
"met the target" with 435 fuel breaks and the one that met it with 77 clearcuts and zero cost.

The arithmetic does not reconcile:

| | |
| --- | ---: |
| `RiskWeightedHazard` curve values | min 0.0000, max 0.1390, mean 0.0142 |
| total block area | 988,816 ha |
| **maximum possible area-weighted sum** | **137,445** |
| account value the simulator reports | **9,419,209** |

A quantity that cannot exceed 137,445 is reported as 9.4 million — 68x its own upper bound.
So the account is not the area-weighted sum its name implies; it is almost certainly summing
per **track** or per **fragment** rather than per block, and a block with several tracks is
counted several times.

Consequences:

- The "target met" results are artefacts of that inflation, not risk reduction. A clearcut
  that raises hazard cannot legitimately meet a risk target; the earlier finding that CC
  "fights the objective" was therefore also reading a broken number.
- The greedy numbers in this note are computed in this repository's own arithmetic
  (area x reduction x p) and are internally consistent, but they are **not** in the same units
  as the ws4 account, so the "optimizer versus greedy" comparison above is void.
- The burn-probability maps, the GeoPackage, and the placement comparison are unaffected:
  they are built from per-block values, not from the account.

What has to happen before this line resumes:

1. Check how ws4 aggregates a **feature** account across tracks and fragments — the patch and
   spread accounts are explicit about area weighting; a feature account may not be.
2. Rebuild the feature so one block contributes once, then re-derive the baseline and confirm
   the reported value is bounded by area x max value.
3. Only then re-run the optimizer and the greedy in one unit system.

Until then the only supported statements are the ones in E7/E9/E10/E16/E20, which do not use
this account.
