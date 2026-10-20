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
- The arrangement effect is small (~2-4%); E2b says why, and E4 must test whether
  it changes the decision.

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


