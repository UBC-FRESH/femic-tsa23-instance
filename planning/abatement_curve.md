# Abatement curve — fuel-treatment subsidy vs risk reduction (TSA23)

**Status:** measured, heuristic ranking, no even-flow harvest constraint in the curve
runs (the even-flow skeleton is a separate result; see §4). Script:
`scripts/abatement_curve.py`. Datasets: `runtime/ws4/compiled_sf_bc` (costs) and
`runtime/ws4/compiled_sf_risk_bc` (risk-weighted account).

## 1. Cost assumptions (updated 2026-10-27)

Anchored on BC programme evidence, replacing the PI point estimates
($20k FT / $5k FB / $3k SF). Sources and alternatives: `config/costs.yaml`.

| treatment | $/ha | source |
| --- | ---: | --- |
| FT (thin + disposal) | 10,000 | FPB/SIR/43 (2015) p.18, provincial average, unchanged 2009–2014 |
| FB (clearcut + disposal) | 7,500 | FNESS 2024/25, Cariboo Fire Centre operational allowance |
| SF (surface fuel) | 3,750 | FNESS 2024/25, maintenance allowance |

Verified per hectare by simulation: FT $10,000.00, FB $7,500.00, SF $3,750.00.
FB remains the cheapest per hazard-hectare ($7,895) versus FT+SF ($17,188).

## 2. Curve

20-year deployment, each treatment scheduled at the first year its age window is open,
ranked by risk-weighted hazard reduction per dollar, simulated on the risk-weighted dataset.
Risk reduction is against the no-treatment mean over 20 years (21,690.9).

| budget ($M) | blocks | treated ha | mean risk-weighted hazard | risk reduction | marginal $M per extra 1% |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | 0 | 0 | 21,690.9 | 0.00% | - |
| 25 | 559 | 2,713 | 21,640.5 | 0.23% | 108.7 |
| 50 | 1,329 | 5,592 | 21,576.8 | 0.53% | 83.3 |
| 100 | 2,902 | 11,469 | 21,463.8 | 1.05% | 96.2 |
| 200 | 4,996 | 22,667 | 21,308.5 | 1.76% | 140.8 |
| 400 | 8,968 | 45,950 | 20,904.1 | 3.63% | 107.0 |
| 800 | 15,667 | 92,980 | 20,124.2 | 7.22% | 111.4 |
| 1,600 | 28,016 | 187,941 | 18,763.2 | 13.50% | 127.4 |
| 3,200 | 52,231 | 393,041 | 16,443.6 | 24.19% | 149.7 |
| 6,400 | 52,901 | 402,851 | 16,400.9 | 24.39% | saturated |

**Findings.**

1. The curve is close to linear up to about $1.6B: roughly **$100–130M buys each
   additional 1% of risk-weighted hazard reduction**. The marginal cost rises at the top
   ($150M/1% between $1.6B and $3.2B) and then saturates.
2. **The model's treatable domain saturates at 402,851 ha** (40.7% of the 988,816 ha
   landbase; 52,901 candidate blocks). Beyond ~$3.3B the ranking pool is exhausted and
   additional budget buys nothing. That ceiling is well below the 892,905 ha that
   paper 1's eligibility rules pass, because the WS4 dataset only carries FB/FT on
   operable managed tracks.
3. The steep first step and the saturation are both real consequences of the candidate
   pool, not of the fire model.

## 3. How this differs from the optimal epsilon-constrained problem

This curve is the **ranking frontier**: candidates are sorted by risk-weighted cost per
hazard-hectare and taken until the budget is spent. It is not the solution of a joint
harvest/treatment optimisation. The evidence that the joint solve is not currently
reachable at this scale is in §4 and in the pilot runs; it is a capability limit, not a
data or formulation limit.

## 4. Even-flow harvest

A four-period (5-year) even-flow harvest schedule is constructible: the seeded constructor
meets a 2.2M m³ per-period level in all four periods (8.8M m³ over 20 years, 599 CC
blocks, 41,293 ha). The model's upper bound from the operable landbase is ~3.2M m³ per
period (12.7M m³ total), so 2.2M is about 70% of the maximum.

The joint solve (even flow + subsidy cap + hazard objective) did not converge:

- annealer from an empty start: 38 blocks, harvest two orders of magnitude below target;
- seeded constructor alone: meets harvest but leaves the subsidy unspent (7 FB blocks in
  200 iterations, hazard down ~1.5%);
- seeded constructor with `--seed-account feature.FuelHazard`: destroys the harvest
  schedule (5k vs 2M m³);
- seed + `--initial-schedule`: identical to the annealer (7 FB blocks).

Runtime is 3.5–6.5 min per run at 40–200 iterations, so the joint grid cannot be brute
forced. The options are a two-stage heuristic (harvest skeleton + ranked treatment
allocation) or block aggregation before the exact/SA lane.

## 5. Caveats

- Heuristic ranking, not optimal. Per-block reductions are not additive; the earlier
  hazard frontier showed projections 40–50% optimistic, so treat the shape, not the
  points, as the result.
- Risk weighting uses the mean-wind burn-probability map (weather averaged, wind not).
- No harvest schedule is merged into these runs: the curve is fuel treatment on its own.
  Adding the even-flow CC skeleton raises the baseline through slash (hazard 2.0 for
  3 years), which the curve does not yet price.
- Costs are BC programme averages; the sensitivity band is $3,750–$13,500/ha, which moves
  every treated-area figure by roughly 0.5–1.8×.
