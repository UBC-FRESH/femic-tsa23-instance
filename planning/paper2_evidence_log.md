# Paper 2 evidence log

Status: living note. Every number here is reproducible from the command and data
named beside it. Companion to `planning/paper2_modelling_plan.md`.

Environment: TSA23 instance (`femic-tsa23-instance`), WS4 `main` >= `a0e4a3d`,
`cffdrs` Python port 0.3.0, FBP via `cffdrs.fbp`.

---

## E1 — Stand-scale treatment effect (FBP, weather-conditional)

Data: `runtime/fire/fbp_stand_curves.csv` (45 AUs x 3 scenarios x 2 states x 21 ages).

Method: FBP per AU (fuel type from VRI species/conifer/dead shares), untreated vs
thinned (cc x0.6, CBH x1.6, crown length x0.7), under FWI scenarios from ERA5
(Open-Meteo): median FFMC 88.4 / BUI 56.1 / FWI 16.8; p90 94.2 / 115.9 / 42.8;
extreme 96.1 / 176.2 / 57.6.

Result, age 60, crown fraction burned (CFB) untreated -> thinned:

| fuel | median | p90 | extreme |
| --- | --- | --- | --- |
| C7 Douglas-fir | 0.12 -> 0.01 | 0.88 -> 0.86 | 0.99 -> 0.99 |
| C3 pine | 0.11 -> 0.00 | 1.00 -> 1.00 | 1.00 -> 1.00 |
| M2 mixedwood | 0.46 -> 0.20 | 0.98 -> 0.98 | 1.00 -> 1.00 |
| C2 spruce | 0.79 -> 0.74 | 1.00 -> 1.00 | 1.00 -> 1.00 |

Head-fire intensity falls 0.9-6% (median weather). **Finding: the treatment
benefit is weather-conditional — real under median weather, overwhelmed at
p90/extreme.**

Caveats: FBP is a *point* fire-behaviour model, not a simulator; single weather
point set (3 points, TSA23 centroid area); allometric crown ratios.

---

## E2 — Landscape pattern / orientation (network spread model)

Data/method: `scripts/landscape_spread.py`. Minimum-travel-time spread (Dijkstra)
on the block topology (`runtime/ws4/topology_tsa23.csv`, 410,823 edges); each
block's traversal time = characteristic length / FBP ROS, anisotropic by bearing
to wind (head 1.0, flank ~0.6, back 0.2); 50 random ignitions; 480 min; p90
weather; wind 225 deg; treated blocks get ROS x factor (standing in for
crown-fire prevention). Patterns are area-matched.

Mean area burned (ha), 20% treated, ROS x0.3:

| pattern | mean burned | p90 burned |
| --- | --- | --- |
| random | 20,298 | 39,483 |
| clumped | 19,870 | 39,404 |
| **barrier** (stripes perpendicular to wind) | **19,640** | **37,637** |

At 10%: random 23,300 / clumped 23,055 / barrier 22,771.

**Finding: arrangement matters beyond treated area (barrier < clumped < random),
growing with treatment strength (ROS x0.3: -2.1% at 20%; earlier x0.6: -1%).**

### E2b — Why the effect is small (diagnostic)

The barrier is **5 stripes ~17 km wide** (not skinny) but perforated (gaps
between stripes) and only **slows** fire. Continuous-band vs striped comparison,
20% treated:

| pattern | ROS x0.3 | ROS x0.05 (near-hard stop) | p90 @ x0.05 |
| --- | --- | --- | --- |
| random | 20,298 | 17,309 | 34,111 |
| barrier (stripes) | 19,640 | **16,549** | **31,743** |
| band (one continuous barrier) | 20,103 | 19,122 | 51,130 |

**Findings:**
- A single continuous barrier is *worse* than random and leaves the p90
  unchanged (51,130 = baseline); it only helps fires starting upwind of it.
- Distributed stripes beat concentration and cut the p90 by ~7%.
- Even a near-hard stop moves the mean only ~4%: the model has no true fuel-break
  stop, so fire routes around gaps and crosses (slower).
- The arrangement signal is clearest in the **tail** (p90), not the mean.

### E2c — Soft vs hard breaks: the ranking flips

Same patterns, 20% treated, p90; treated blocks either slow fire (ROS x0.3) or
are impassable (ROS x0.0).

| pattern | ROS x0.3 (slow) | ROS x0.0 (impassable) |
| --- | --- | --- |
| random | 20,298 | 16,690 |
| clumped | 19,870 | **15,742** (-5.7%) |
| barrier (perp. wind) | **19,640** | 16,118 (-3.4%) |

p90 at x0.0: random 32,735; clumped 31,626; barrier 31,609 (clumped and barrier
tied, both ~3.4% below random).

**Findings:**
- A true (impassable) break roughly **doubles** the arrangement effect
  (clumped -5.7% vs -2.1% at x0.3). Part of the earlier small effect was the
  soft treatment, not the landscape.
- The **ranking flips**: with soft breaks, orientation (barrier) wins; with hard
  breaks, distribution (clumped) wins and orientation's edge disappears. So
  "which pattern is best" depends on the treatment's actual effect on spread.
- Implication for the bridge: the account(s) must carry **distribution** and,
  for soft treatments, **orientation**; a single size-only or connectivity-only
  metric will not cover both regimes.

### E2d — The model's own hazard (FT 0.4 / SF 0.2 / FB 0.05)

Same patterns, 20% treated, p90, with the spread multiplier taken from the model's
`feature.FuelHazard` (not a hand-set flag):

| treatment | random | clumped | barrier | p90 random | p90 barrier |
| --- | --- | --- | --- | --- | --- |
| FT (0.4) | 21,096 | 20,669 | **20,583** | 41,527 | 40,355 |
| SF (0.2) | 19,406 | 18,897 | **18,581** | 38,028 | 35,428 |
| FB (0.05) | 17,309 | 16,582 | **16,549** | 34,111 | 31,743 |

**Findings:**
- Arrangement helps for every treatment (barrier <= clumped < random), and the
  effect **grows with treatment strength**: barrier vs random is -2.4% (FT),
  -4.3% (SF), -4.4% (FB) on the mean, and -2.8% / -6.8% / -6.9% on the p90.
- At the model's **near-null** FB (0.05), barrier still edges clumped on the mean
  (-0.2%) and clearly wins on the p90 (-2.8%). The earlier E2c **flip** (clumped
  best) only appears at a **true impassable stop (0.0)** — i.e. a near-null
  treatment still lets fire cross slowly, so orientation keeps an edge. A
  genuinely cleared break is what changes which pattern wins.
- Implication: the bridge account must represent both **distribution** and
  **orientation**, and the weight/interpretation depends on how close to
  impassable the treatment really is.

**Verification (2026-10-20).** E2, E2b, E2c and E2d were re-run through the same CLI
path (`scripts/landscape_spread.py`, 50 ignitions, p90, wind 225°, seed 1) as a
repeatable check: `scripts/verify_legacy_evidence.py` compares 19 recorded cells against
a 1.0 ha tolerance. **All 19 reproduce** (mean and p90), so these entries are verified
rather than merely inherited.

They predate the shared-ignition fix and are **not** affected by it: the block table and
the seed are fixed while the pattern varies, so every pattern sees the same ignition
draw. The confound was specific to the newer matched-footprint harness, which rebuilt
the RNG per pattern.

They are, however, **p90-weather-specific**. E9 and E10 show the ordering reverses at
median weather, so the E2/E2d statements must not be generalised without naming the
scenario.

### E2e — Matched-footprint bridge test (the decisive one)

The earlier patterns were area-matched but not **footprint-matched**: they occupy
different geographic extents, so a difference could be *where*, not *how*. This
test fixes a contiguous **20,000 ha footprint**, treats **20%** of it with FB
(hazard 0.05), ignites **40** fires inside it, p90, wind 225°, and compares the
fire outcome with connectivity metrics of the treated/untreated partition
(`scripts/bridge_matched_footprint.py`).

| pattern | mean burned (ha) | largest_component | directed_largest_reach | directed_mean_reach |
| --- | --- | --- | --- | --- |
| **barrier** | **4,833** (best) | 1,060 | **471** | **107** |
| clumped | 5,250 | **984** | 765 | 178 |
| random | 6,088 (worst) | 1,466 | 913 | 253 |

**Findings:**
- Fire rank: **barrier < clumped < random**.
- **Directed** reach (`directed_largest_reach`, `directed_mean_reach`) reproduces
  it exactly (**agree = True**).
- **Undirected** `largest_component` does **not** (clumped first), and a raw
  `aligned_edge_cut` does not (clumped lowest).
- So the account the bridge needs is a **directed, downwind reachability** metric —
  not undirected connectivity and not patch size. This is the concrete spec for
  the WS4 account, and it survives the footprint confound.

### E6 — Response surface: when does directed reach predict the outcome?

Sweep of the matched-footprint test: 3 weather scenarios x 3 treat fractions
(10/20/30%) x 3 patterns, FB (0.05), 40 ignitions, 480 min
(`runtime/fire/response_surface.csv`).

Pooled across all 27 points, `burned ~ directed reach` gives **R2 = 0.08**
(undirected 0.10) — **weather dominates**, so a single pooled fit is meaningless.
Within a scenario:

| scenario | R2 (directed reach) | burned range (ha) | best pattern by fraction |
| --- | --- | --- | --- |
| p90 | **0.906** | 3,634-8,549 | 0.1 random (marginal), 0.2/0.3 **barrier** |
| extreme | **0.656** | 6,478-15,647 | 0.1 barrier, 0.2 **clumped**, 0.3 barrier |
| median | 0.164 | 90-144 | random (differences negligible in absolute terms) |

**Findings:**
- **Directed reach predicts well when fire is severe and treatment substantial**
  (p90 R2 0.91; extreme 0.66).
- At **median** weather the fire is small (90-144 ha) and arrangement barely
  matters; random can be marginally better by intercepting more ignitions, but
  the absolute effect is negligible.
- At a **sparse 10% treatment**, arrangement is marginal even at p90.
- The best pattern is **scenario-dependent** (barrier vs clumped flips), so the
  bridge account must be **scenario-conditioned**: weight it by the fire-weather
  scenario (or apply it only under severe weather with sufficient treatment), not
  as a fixed linear term.

**Reproducible oracle bundle** (`scripts/export_bridge_footprint.py`): the three
schedules are laid out inside a fixed 1,877-block / 20,018.95 ha footprint, and the
bundle exports that footprint topology (`src_block,dst_block,distance_m,bearing_deg`),
block representative points, per-block base hazard, the three schedules, and
`oracle.json`. Verified: every footprint block is flammable at period 0
(`feature.FuelHazard` = 1.0); a scheduled FB block reads 0.05 and acts as a barrier
under the WS4 membership convention (member when value > threshold).

| pattern | treated blocks | directed_largest_reach | directed_mean_reach | undirected largest_component | mean burned (ha) |
| --- | --- | --- | --- | --- | --- |
| barrier | 291 | 471 | 107.3 | 1,060 | 4,833 |
| clumped | 356 | 765 | 178.5 | 984 | 5,250 |
| random | 359 | 913 | 253.2 | 1,466 | 6,088 |

The undirected component ranks clumped < barrier < random and fails; directed reach
ranks barrier < clumped < random and agrees with the fire model. `directed_edge_cut`
(191 / 134 / 933) is not monotone and is diagnostic only.

---

## E3 — Bridge test: does WS4 see the fire benefit?

Data/method: `scripts/ws4_bridge_test.py`; WS4 patch account
`patch.ft` (criteria `product.Treated.managed.FT`, size classes 10/50/150/400/inf,
search distance 0) on the same treated blocks.

| pattern | mean burned (fire) | WS4 patches | WS4 400+ share |
| --- | --- | --- | --- |
| barrier | **19,640** (best) | 2,035 | **40.2%** (largest) |
| clumped | 19,870 | 2,832 | 23.1% |
| random | 20,298 (worst) | 2,773 | 26.0% |

`fire rank: [barrier, clumped, random]`; `size rank: [barrier, random, clumped]`;
**agree = False**.

**Finding (negative): WS4 patch-size accounts cannot express the fire benefit —
the barrier is best for fire but has the largest 400+ ha share. The needed
account is connectivity/orientation.** This is the measured ceiling that defines
the WS4 extension (`ws4-spread-connectivity-account-prompt.md`).

---

## E4 — The budgeted study (corrected targets)

Data: `runtime/fuel_ft_proto/study_targets_v2.yaml` (both bounds on
`product.FuelTreatmentCost`, `year: 4`, `period_width: 5` -> years 0-4; hectares =
cost / $20,000). Horizon 5 years.

| run | horizon cost | hectares | objective | blocks | time_limit_reached |
| --- | --- | --- | --- | --- | --- |
| unseeded (500 iters, 3 min, 8 threads) | $3.55M | **178 ha** | 76,449,037 | 163 | False |
| seeded (`--seed-greedy`, 10 min, 8 threads) | $200.0M | **10,000 ha** | **0.0** | 1,713 | False |

**Finding: `--seed-greedy` closes the aggregate-target gap (76.4M -> 0.0), meeting
the 4,000 ha floor and the $200M budget.**

Original-target handoff run (seeded, for comparison): FT account 39,999.8 (floor
16,000 met), cost $199,999,193 (budget met), objective 0.0, 714 blocks.

### E4b — Target-specification defects found

1. `year` is the period's **end** (`cell_years()`): `year: 0` with no
   `period_width` reads year 0 only, so on a 5-year horizon four years scored
   nothing toward the floor.
2. `product.Treated.managed.FT` **is not treated hectares**: the budget-capped
   schedule treats 9,983 ha at $199.7M but the account reads **39,933 (4.0x)**.
   The cost account is the clean measure. So the original "16,000 ha" floor was
   really ~4,000 ha.
   (Recorded for WS4: `ws4/ws4/tmp/ft-area-account-finding.md`.)

---

## Reproduction map

| artifact | path |
| --- | --- |
| FBP stand curves | `scripts/fbp_stand_curves.py` -> `runtime/fire/fbp_stand_curves.csv` |
| FWI scenarios | `scripts/fire_weather_scenarios.py` -> `runtime/fire/fwi_scenarios.csv` |
| Block topology | `scripts/build_block_topology.py` -> `runtime/ws4/topology_tsa23.csv` |
| Landscape spread | `scripts/landscape_spread.py` -> `runtime/fire/*.json` |
| Bridge test | `scripts/ws4_bridge_test.py` |
| Study targets (corrected) | `runtime/fuel_ft_proto/study_targets_v2.yaml` |
| Study runs | `runtime/ws4/ft_v2_unseeded/`, `runtime/ws4/ft_v2_seeded/` |
| WS4 findings/prompts | `/srv/shared-data/gep/ws4/tmp/` (dead drop) |

## Caveats (do not quote the numbers without these)

- The spread model is a **simplification**: no suppression, isotropic within a
  block, a flat treated-ROS factor standing in for crown-fire prevention, one
  wind direction. It is a vehicle for the bridge, not a fire-risk product.
- FBP fuel typing is rule-based from VRI shares; it should be validated against
  the BC provincial FBP fuel-type raster.
- Weather is ERA5 daily proxies at three points, not station observations.
- The **size and sign of the arrangement effect depend on the weather scenario**: at
  median-to-p80 the barrier is 8-38% *worse* than the best pattern; at p85 and above it
  is best or tied (E9, E10). Any statement of the form "arrangement X is better" must
  name its weather. The old "small, ~2-4%" summary applied to a single p90 seed and is
  superseded.

## Detailed methods

`planning/bridge_experiment_log.md` records, per experiment, the design, inputs, exact
command, outputs, runtime, and the corrections log. Use it to regenerate any table;
`runtime/` is gitignored, so no result is committed and every one is reproducible only
through that file.

**E7 corrects E2e and E6.** The single-seed matched-footprint test drew a fresh
ignition set for each pattern, so "pattern" and "which blocks burned" moved together.
Re-run with one ignition set shared by all three patterns on the same footprint
(`scripts/bridge_matched_footprint.py --footprint-seed 1 --seed N`, five seeds,
`runtime/fire/p16_seed_sweep.csv`):

| seed | barrier mean | clumped mean | random mean | barrier p90 | clumped p90 | random p90 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 5,116 | 4,732 | 7,050 | 7,227 | 9,181 | 12,446 |
| 2 | 4,632 | 7,076 | 6,844 | 7,025 | 14,014 | 11,820 |
| 3 | 4,561 | 5,837 | 5,218 | 6,709 | 12,219 | 9,505 |
| 4 | 5,272 | 4,766 | 6,818 | 7,532 | 10,747 | 11,976 |
| 5 | 5,506 | 5,881 | 6,857 | 7,564 | 12,514 | 11,431 |

- The **mean ranking is not stable**: barrier first in 3/5 seeds; clumped best in seeds
  1 and 4; in seeds 2 and 3 clumped is worse than random on mean and p90.
- The **barrier is best on p90 in 5/5 seeds**, by 30-45%. That is the stable result.
- Directed largest reach puts the barrier first 5/5 but matches the mean ordering only
  3/5, and the mean is the unstable target, so **E2e's "directed reach reproduces the
  fire rank" is not supported as stated**. Treat it as a single-seed coincidence
  produced by the ignition confound.
- The 90-degree undirected compartment reproduces the p90 ordering 5/5; the 60-degree
  cone 3/5 (consistent with WS4 P15's cone-width caveat).
- The E6 response surface inherits the same confound; its within-scenario R2 should be
  re-measured with a shared ignition set before it is quoted.

**Treatment factors actually used (do not conflate them).** `TREATMENT_HAZARD["fb"] = 0.05`,
so the matched-footprint runs above apply a **20x slowdown** to treated blocks, not the
0.3 used by the published landscape bridge. The 0.3 figure belongs to the 177k-ha and
54k-ha mask runs. The 20% local result therefore already sits close to a hard stop: even
at a 20x slowdown, only the tail responds stably.


**Do not build the Paper 2 bridge on a mean-burned ranking at 40 ignitions.** Either
raise the ignition count or use the tail statistic.

**E8 — the oracle bundle's topology was ambiguous, and is fixed.** The first export
wrote one row per undirected pair with a single `bearing_deg`. Read as a directed edge
list — which is what the file looks like — it silently drops every edge stored in the
upwind orientation and returns **47 / 47 / 37 blocks** (means 4.92 / 5.04 / 3.89)
instead of **471 / 765 / 913** (107.33 / 178.49 / 253.20). Both figures were reproduced
on the same data; the difference is entirely the file's ambiguity. The export now
writes both orientations, each with its own bearing (12,592 rows), so the simple
directed reading and the undirected-adjacency reading agree. Caught by WS4 in
`femic-tsa23-instance#13`.

**E9 — sensitivity screen: the arrangement ranking is weather-conditional, not universal.**
108 cells (`scripts/sensitivity_screen.py`, `runtime/fire/sensitivity_screen.csv`):
fixed 1,877-block / 20,019 ha footprint, three patterns, 40 ignitions, wind 225,
density {0.05, 0.10, 0.15, 0.20} x weather {median, p90, extreme} x treated ROS
multiplier {0.05, 0.30, 1.00} x 3 seeds. Footprint fixed across all cells.

*Control.* At multiplier 1.00 the patterns are identical to the last decimal (0.0%
spread, barrier never best) — the harness shows no phantom signal.

*Effect size scales with density* (spread across the three patterns, p90, mean of
scenarios and seeds):

| density | multiplier 0.05 | multiplier 0.30 |
| --- | ---: | ---: |
| 0.05 | 6.1% | 4.7% |
| 0.10 | 15.3% | 6.0% |
| 0.15 | 29.9% | 12.9% |
| 0.20 | 35.6% | 12.7% |

*Weather decides which pattern wins.* Barrier excess over the best pattern (median
over seeds; 0 means the barrier is best):

| density / multiplier | median | p90 | extreme |
| --- | ---: | ---: | ---: |
| 0.15 / 0.05 | **+16.9%** | 0.0% | 0.0% |
| 0.20 / 0.05 | **+21.3%** | 0.0% | 0.0% |
| 0.15 / 0.30 | **+12.6%** | +2.7% | 0.0% |
| 0.20 / 0.30 | **+12.4%** | 0.0% | +0.3% |

At **median** weather the barrier is the *worst* arrangement at every density above
5%, by 12-26% relative. At **p90 and extreme** it is best or tied. Across all 108 cells
the single most common ordering is random < clumped < barrier (49 cells on the mean,
52 on p90), so "barrier is best" is only true in the severe-weather half of the grid.

*Absolute stakes matter for reading those percentages.* Median burned area per
ignition: ~120 ha at median weather, 7,100-9,700 ha at p90, 14,850-17,150 ha at
extreme. The 12-26% penalty at median is therefore a few tens of hectares, while the
zero-penalty result at p90 concerns thousands. Evaluate on the weather that carries
the area.

Consequence: E2e/E6/E7 are all weather-specific. Any statement of the form
"arrangement X is better" must name the weather scenario.




**E10 — the crossover: coverage wins below p80, the barrier wins above p85.**
60 cells (`scripts/sensitivity_screen.py`, `runtime/fire/weather_crossover.csv`): the
fire-season ladder from E9's scenario builder (quantiles 0.50-0.98, FWI 16.8-57.6),
density 0.15 and 0.20, treated multiplier 0.05, three seeds, fixed footprint and
shared ignitions. The original three scenarios reproduce byte-identically, so the
ladder is an extension, not a rebuild.

Barrier excess over the best pattern (%), p90 burned, median over seeds:

| scenario (FWI) | density 0.15 | density 0.20 | p90 burned (ha) |
| --- | ---: | ---: | ---: |
| median (16.8) | +16.9 | +21.3 | 231 |
| p60 (21.8) | +18.7 | +34.3 | 803 |
| p65 (24.7) | **+33.0** | **+38.3** | 1,349 |
| p70 (27.8) | +20.6 | +30.2 | 2,101 |
| p75 (31.0) | +14.0 | +14.3 | 3,117 |
| p80 (34.5) | +8.2 | 0.0 | 4,694 |
| p85 (38.4) | 0.0 | 0.0 | 7,791 |
| p90 (42.8) | 0.0 | 0.0 | 9,988 |
| p95 (49.9) | 0.0 | 0.0 | 14,680 |
| extreme (57.6) | 0.0 | 0.0 | 17,268 |

Mean burned shows the same crossover at p80 (+5.9% at p75, 0.0 at p80 and above).

Two regimes, with a sharp transition between p80 and p85 (FWI 34.5 -> 38.4):

- **Coverage regime (<= p80).** Scattering treatment beats a barrier, and the penalty
  peaks at **p65** (+33 to +38%), not at the median: at median the fire is too small for
  arrangement to matter (231 ha p90), while at p65 it is large enough to matter.
- **Barrier regime (>= p85).** The barrier is best or tied at every density tested, where
  the p90 fire is 7,800-17,300 ha.

The practical reading: arrangement is worth optimizing only if the landscape is managed
for the p85-and-above tail; below that, treat for coverage. That is a decision statement
the student can test, not a claim about the paper.

**E11 — the FT dataset recompile, and a second duplication defect in our own scripts.**
Rebuilt with WS4 `main` at `c9efec6` (builder fix `8f0f6d4`):

| dataset | before | after |
| --- | ---: | ---: |
| `products.parquet` rows (FT base) | 4,947,045 | 3,431,580 |
| redundant `(track, treatment, label, curve_id)` rows | 1,515,465 | 0 |
| keys with more than one curve (legitimate per-AU components) | 85,532 | 85,532 |

**Acceptance.** On `ft_cap.csv` at year 0: `product.Treated.managed.FT` =
**9,983.3605 ha**, `product.FuelTreatmentCost / 20,000` = **9,983.3605 ha**, ratio
**1.0000** (was 4.0000, FT = 39,933.4419). The old dataset also emitted the loader
warning naming 1,515,465 redundant rows; the recompiled one is silent.

**Second defect, ours.** Rebuilding the derived datasets exposed a duplication bug in
`add_fuel_break_treatment.py` and `add_surface_fuel_treatment.py`: they copy a
destination track's products and retag the treatment, so rows that differed only by
treatment (FT vs CC) collapse onto one FB key. That added **28,609** duplicate rows to
the FB dataset. Fixed with the builder's rule — drop exact duplicate keys, keep
different curves — and both scripts now print the count. FB reports 28,609 dropped; SF
reports 0 on clean input.

**The bridge is unaffected.** `feature.FuelHazard` is identical between the old and the
recompiled `compiled_fb_haz` (158,437 tracks compared, max delta 0.0; 15,179 FB tracks at
0.05, 143,258 at 1.0), so the oracle bundle, the masks and the E7-E10 results stand
unchanged.

Old datasets are archived under `runtime/ws4/_superseded_dup_product_rows/` (gitignored).

**E12 — WS4's spread-connectivity account reproduces the measured oracle exactly.**
`scripts/verify_spread_account.py`, WS4 `main` at `c9efec6`, dataset
`runtime/ws4/compiled_ft_econ` (recompiled, no duplicate product rows), bearing 225,
tolerance 60, `search_distance=None`, each pattern's own `bridge_{pattern}_sched.csv`
applied at period 0:

| pattern | treated blocks | treated ha | largest (ha) | percolation (ha) |
| --- | ---: | ---: | ---: | ---: |
| barrier | 3,483 | 54,368.1 | 82,874.4 | 25,696.8 |
| clumped | 3,557 | 55,836.6 | 105,020.4 | 32,250.4 |
| random | 3,366 | 53,697.0 | 196,766.6 | 50,280.8 |

Every value matches the WS4 side's table to the decimal, including the treated block
counts. Run time 4 m 12 s.

**Two harness bugs found while getting there, both mine:**

1. The files in `bridge-masks-dedup/` are the *result* of applying each pattern's
   schedule, not an input to it. Feeding a mask back as a schedule re-treats blocks that
   are already treated, and the criterion falls below 0.5 for many of them (clumped read
   1,844 treated blocks instead of 3,557).
2. `Simulator.run()` mutates treatment state. Reusing one simulator across the three
   patterns made each inherit the previous one's treatments; barrier was correct only
   because it ran first. A fresh `Simulator.from_dataset()` per pattern fixes it.

Both are recorded in `scripts/verify_spread_account.py` where they bit.

**What this does and does not establish.** The account's *values* are verified against an
independent implementation. Its *fire-response validity* is not: E7/P16.1 showed that at
the footprint WS4 can actually treat, the fire ranking is inside seed noise. E12 is a
correctness check on the metric, not a revival of the bridge claim.

**E13 — the hazard account ignored FT, and the published bundle was wrong.**
`complete_hazard_feature.py` assigned the thinned (0.4) hazard to states starting
`cc_pl_ct`, but this model's states are `cc_pl_ft30/40/50/60`. The rule never fired, so
every thinned track read baseline 1.0: the hazard account could not see FT at all, and a
scheduler targeting it would have valued FT at zero benefit.

Measured on `compiled_fb_haz` after the fix:

| hazard | tracks before | tracks after |
| --- | ---: | ---: |
| 1.0 baseline | 143,258 | 85,526 |
| 0.4 thinned (FT) | 0 | 57,732 |
| 0.05 fuel break (FB) | 15,179 | 15,179 |

`compiled_sf` adds 100,388 tracks at 0.2 (surface fuel).

**The bridge is unaffected.** All 1,877 footprint blocks read 1.0 in both the old and the
rebuilt dataset (compared block by block, max delta 0.0), so the oracle's 471 / 765 / 913
and the matched-footprint results stand.

**The published bundle was stale and was republished** as `data-2026-10-20.1`
(`sha256 58af953e...`), with `data-2026-10-20` marked superseded rather than silently
overwritten.

**E14 — the clearcut slash spike is now represented, as a parameterized scenario.**
`feature.FuelHazard` previously read 1.0 for `cc_pl` (fresh clearcut), which made an
untreated harvest look as safe as old forest and flattered every treatment comparison.

Added: `cc_pl` = 2.0 for 3 years, decaying to 1.0 by year 10 — 20,530 tracks. Chosen
inside the FBP slash range (S-2 ~2.3x at median weather, S-3 ~2.7x) and between BC's
1-2 year abatement cycle and the ~13 year slash-loading evidence. Derivation, the FBP
table, the duration evidence and a contrary national finding (harvested stands ~28%
*lower* first-fire hazard) are in `planning/literature_slash_hazard.md`.

**The bridge is unchanged**: the oracle still reproduces 471 / 765 / 913 after the
rebuild, because the account uses hazard only for membership (> 0.5) and the spike only
raises a value already above it. The fire model uses `TREATMENT_HAZARD` constants, not the
feature.

Known limitation: FBP's slash/timber ratio is weather-dependent (5.5x at median weather
for S-1, 1.4x at extreme), while the model applies a constant multiplier. If the
sensitivity shows the ranking moving, the answer is a weather-conditioned hazard, not a
better constant.

**E15 — the spread model can now read `feature.FuelHazard`, and the slash state does not
change the ranking.** `landscape_spread.load_block_hazard` returns the area-weighted
hazard per block at its current age; `run_matched_footprint.py --hazard-dataset` uses it
instead of a flat 1.0.

**Equivalence gate.** With the pre-slash dataset (every block 1.0), the barrier mask
reproduces the published run exactly: **19,640.448328143004**, p90 37,637.13355349601.
The refactor is therefore not silently changing the model.

**With the slash state active** (current `compiled_fb_haz`, `cc_pl` = 2.0 for 3 years):

| pattern | mean burned (ha) | p90 (ha) |
| --- | ---: | ---: |
| barrier | 31,241.1 | 54,512.2 |
| clumped | 31,738.5 | 58,879.5 |
| random | 32,625.2 | 60,152.4 |

Ranking **barrier < clumped < random** on both statistics — unchanged. The magnitudes rise
about 59%, and the arrangement effect grows from 3.2% to 4.2% (barrier vs random), i.e.
the slash state amplifies the arrangement signal rather than reversing it.

**Scope of the change.** The hazard-fed path is opt-in. The default remains the
`TREATMENT_HAZARD` constants, so E2, E7, E9 and E10 stand exactly as recorded; E15 is a
variant that shows what the recorded results were missing.

**E16 — the arrangement ranking is insensitive to the slash parameters.**
`scripts/slash_sensitivity.py`, 4 multipliers {1.5, 2.0, 3.0, 5.0} x 3 decay windows
{5, 10, 20} years x 3 patterns, 50 ignitions, the published landscape masks.

| multiplier | decay 5 | decay 10 | decay 20 |
| --- | --- | --- | --- |
| 1.5 | barrier < clumped < random (3.6%) | same (3.9%) | same (3.9%) |
| 2.0 | same (3.8%) | same (4.1%) | same (4.4%) |
| 3.0 | same (3.9%) | same (4.4%) | same (4.7%) |
| 5.0 | same (4.2%) | same (4.2%) | same (4.1%) |

(percentages are the spread between the best and worst pattern)

**The ranking holds in 12 of 12 combinations.** The arrangement effect stays between 3.6%
and 4.7%, against 3.2% with no slash state at all. So the paper does not have to defend a
particular slash multiplier to keep its arrangement conclusion: a 3.3x range in the
contested parameter moves the effect by about one percentage point.

**A harness bug was caught first, and it matters.** The initial run reported
`random < clumped < barrier` with a 40% spread — the reverse of every other result. The
cause was that `ros_eff` was reset once per parameter combination rather than once per
pattern, so each pattern inherited the previous pattern's treated blocks; the last pattern
read as fully treated. A 40% spread was the tell. After the fix the spread is 3.6-4.7%,
consistent with E2 and E15. Recorded because a plausible-looking result with a wrong
harness is the exact failure mode this log exists to prevent.

**E17 — the hazard-objective run fails, and the reason is not the optimizer.**
`compiled_sf`, 5-year horizon, target `feature.FuelHazard` at year 4 <= 970,000 against a
measured empty-schedule baseline of **992,334** (year 4; year 0 is 1,015,743), with a
$100M budget split as FT $50M / FB $25M / SF $25M.

Result: hazard 991,770 — a 0.06% reduction, target missed by 21,770 (penalty). The
schedule contained 57 CC, 84 FB, 22 FT and 15 SF blocks, but **only FT and CC produced
accounts**:

| account | rows | sum |
| --- | ---: | ---: |
| `product.FuelTreatmentCost` | 22 | 5,285,691.7 |
| `product.FuelBreakCost` | 0 | 0 |
| `product.SurfaceFuelCost` | 0 | 0 |

84 FB and 15 SF entries were inert, with no warning. Minimal reproductions are in
`femic-tsa23-instance#18`: a single FB on an operable block produces nothing, and CC then
FB still produces nothing.

**Why the target was unreachable anyway.** At the instance's cost and hazard levels the
cost per hazard-hectare of reduction is roughly: fuel break $5,263, thinning $33,333.
Closing a 22,334 hazard-ha gap therefore needs ~$118M of FB — and FT cannot do it under any
plausible budget. So the *ranking* of treatments by hazard-per-dollar is already
informative even though the optimizer cannot yet express it.

> **Corrected by E20.** This entry originally listed surface fuel at $3,750 per
> hazard-hectare, as if SF could be applied alone. It cannot: SF follows a thinning, so the
> FT+SF sequence costs $28,750. See E20 and
> `planning/hazard_cost_effectiveness.md`.

**Blocked on `#18`.** The treatment-mix question cannot be answered until an inapplicable
scheduled treatment is either refused loudly or not offered.

**E18 — FB and SF produced nothing because their products were on the wrong track.**
WS4 resolves a product at apply time by `(track the treatment is applied to, treatment
label)`. The FT layer writes its products on the source track, which is why thinning
worked. `add_fuel_break_treatment.py` and `add_surface_fuel_treatment.py` copied the
products onto the **destination** track instead, so the lookup missed every time and the
treatment was applied with no accounting and no warning.

| product | treatment | on source track | on destination track |
| --- | --- | ---: | ---: |
| `product.FuelTreatmentCost` | FT | 14,433 | 0 |
| `product.FuelTreatmentCost` | FB | 0 | 14,433 |
| `product.FuelBreakCost` | FB | 0 | 15,179 |
| `product.SurfaceFuelCost` | SF | 0 | 100,388 |

**Fix.** FB now copies the CC harvest products onto the source track and retags them FB,
because an FB is a clearcut. SF produces only its cost, on the FT destination track: a
surface-fuel treatment yields no timber, and copying the FT yields would double-count the
thinning.

**Verified on single blocks.** FB on block 3994: `product.FuelBreakCost` = $47,728.94 for
9.5458 ha = $5,000/ha. FT then SF on block 52103: `product.FuelTreatmentCost` =
$392,929.52 for 19.6465 ha = $20,000/ha, and `product.SurfaceFuelCost` = $58,939.43 the
following year = $3,000/ha.

**The bridge is unchanged**: the oracle still reproduces 471 / 765 / 913 after the
rebuild, because only product rows moved, not the hazard features.

**E19 — with FB and SF accounting fixed, the binding constraint is search scale.**
Re-run of the hazard objective on the corrected `compiled_sf` (E18):

| account | value at year 4 |
| --- | ---: |
| `product.FuelTreatmentCost` | 5,285,691.7 |
| `product.FuelBreakCost` | 3,094,954.6 |
| `product.SurfaceFuelCost` | 401,997.2 |

FB and SF now record real costs. Total spend is **$8.78M of a $100M budget**, so the budget
is not what stops the run.

**Hazard is unchanged at 991,770** — the same as the buggy run. That is consistent: the
state transitions were always applied, so the hazard moved; only the accounting was
missing. The missing products did not change the landscape, they changed the score.

**What the gap actually needs:**

| treatment | hectares to close 22,334 hazard-ha | cost |
| --- | ---: | ---: |
| surface fuel | 27,918 | $83.8M |
| fuel break | 23,509 | $117.5M |
| thinning | 37,223 | $744.5M |

The run treated roughly **1,000 ha** — FT 264 ha, FB ~619 ha, SF ~134 ha — against the
~28,000 ha of surface fuel the target requires. That is a factor of about 27.

**Conclusion.** The hazard target is feasible within the stated budget (surface fuel at
$83.8M), but the optimizer schedules 178 blocks where ~2,900 are needed. This is the same
class of failure as P14: aggregate targets need thousands of moves and the annealer
produces hundreds. The earlier `--seed-greedy` work addressed the aggregate-area case; the
hazard case inherits the same limit.

So the treatment-mix question is now answerable in principle and blocked in practice by
search scale, not by physics or by budget.

**E20 — a greedy hazard schedule, and a correction to the cost-per-hazard ranking.**
`scripts/greedy_hazard_schedule.py`: 39,407 operable candidates on `compiled_sf`, ranked by
cost per hazard-hectare, taken until the $100M budget is spent.

Result: **2,969 fuel-break blocks, $99,999,852**, simulated hazard at year 4 =
**973,334** (1.91% below the 992,334 baseline), against the 970,000 target (2.25%). Missed
by 3,334.

Two findings.

**1. The target is infeasible at $100M.** The modelled cost is $5,350 per hazard-hectare
(the greedy's own average), so closing 22,334 hazard-ha needs about **$118M**. The earlier
analytic figure of $5,263 was close; the budget, not the optimizer, is the limit.

**2. Correction to E17's cost-per-hazard table.** It listed surface fuel at $3,750 per
hazard-ha, as if SF could be applied on its own. It cannot: SF's source track is the FT
destination, so it only follows a thinning. The true cost of an FT+SF sequence is
($20,000 + $3,000) / 0.8 = **$28,750 per hazard-ha**, not $3,750. The corrected ranking is:

| intervention | cost per hazard-ha |
| --- | ---: |
| fuel break (FB) | **$5,263** |
| thinning then surface fuel (FT+SF) | $28,750 |
| thinning (FT) | $33,333 |

So fuel breaks are the only efficient hazard buy on this landscape, which is why the greedy
selects nothing else. E17's surface-fuel row should be read with this correction.

**3. The search gap is now quantified.** For the same $100M: the annealer reached 991,770
(0.06% reduction, 178 blocks); the greedy reached 973,334 (1.91%, 2,969 blocks) — **30x
more hazard reduction**. That is the scale `ws4#165` has to close.

Caveat: the greedy's projection (971,478) overshot the simulated result (973,334) by 1,856,
so per-block reductions are not perfectly additive — treatments shift ages and interact.
The simulation is the number to trust.
