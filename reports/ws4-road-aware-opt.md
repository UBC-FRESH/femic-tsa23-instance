# TSA 23 road-aware optimizer scenario

Date: 2026-10-29

This is the first road-aware WS4 optimization scenario for TSA 23.  The harvest
targets are unchanged; one route-build budget is added as a scenario bound.

## Configuration

- Dataset: `runtime/ws4/compiled_sf_risk`
- Route config: `config/ws4/route_c5_road.yaml`
  - c5 network, `initial_roads: all` (planned network; build is charged when a
    segment is first used)
  - build, haul, and maintenance accounts per mill
  - duplicate accounts `route.Total.build`, `route.Total.maintain`,
    `route.Total.haul`
- Targets: `config/ws4/risk_road_objective.yaml`
  - existing risk/fuel targets unchanged
  - `route.Total.build` maximum **10,000,000 CAD** in period 1
  - the 10 M bound is a **benchmark scenario**, not a policy recommendation
- Initial schedule: `runtime/ws4/schedule_baseline.csv`
- 5 years, 100 iterations, seed 1, 1 worker, 5-minute limit

## Result

- Status: `ok`
- Blocks scheduled: 2,031
- Iterations: 100; time limit reached
- Unrouted route rows: **0**
- `route.Total.build`: **27,409,188.40 CAD** (target 10,000,000; above)
- `route.Total.haul`: 29,021,723.74 CAD
- `route.Total.maintain`: 11,089,934.08 CAD
- First-period total route expense: 67,520,846.21 CAD
- `feature.RiskWeightedHazard`: 21,965.48 (target 21,582; above)

For comparison, the five-iteration all-open run had build 28,793,029.26 CAD and
hazard 21,991.93.  The 100-iteration scenario reduced build by about 1.38 M CAD
and hazard by 26.4 units, but did not approach the 10 M build bound.

## What this shows

- The all-open planned network is fast enough for a road-account-aware
  optimization run; build is charged for potential roads when first used.
- The 10 M build bound is not achievable with this schedule/search budget.
- A real road-aware study needs a defensible budget and a longer/search budget;
  the current result is a scenario, not a recommendation.

## Rejected alternatives

- `initial_roads: existing` on the full 465k-segment network: 10 blocks took
  100 seconds; not viable for optimizer iterations.
- A reduced network built only from the roads used by the risk schedule: not
  connected for new schedules; it produced 7,587 unrouted rows and was rejected.

No WS4 objective, constraint, growth, or solver code was changed.  The target
configuration is a scenario file.
