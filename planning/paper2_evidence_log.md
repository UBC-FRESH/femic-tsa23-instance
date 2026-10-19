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
| WS4 findings/prompts | `/srv/shared-data/gep/ws4/ws4/tmp/` |

## Caveats (do not quote the numbers without these)

- The spread model is a **simplification**: no suppression, isotropic within a
  block, a flat treated-ROS factor standing in for crown-fire prevention, one
  wind direction. It is a vehicle for the bridge, not a fire-risk product.
- FBP fuel typing is rule-based from VRI shares; it should be validated against
  the BC provincial FBP fuel-type raster.
- Weather is ERA5 daily proxies at three points, not station observations.
- The arrangement effect is small (~2-4%); E2b says why, and E4 must test whether
  it changes the decision.
