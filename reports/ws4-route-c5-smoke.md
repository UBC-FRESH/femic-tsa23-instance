# TSA 23 c5 route smoke run

Date: 2026-10-29

This records the first WS4 optimizer run using the planned c5 road network in
the TSA 23 instance.  It is a smoke/validation run, not a converged plan.

## Configuration

- Dataset: `runtime/ws4/compiled_sf_risk`
- Targets: `config/risk_objective.yaml`
- Route config: `config/ws4/route_c5.yaml`
- Route tables: `runtime/ws4/roads_c5/` (generated from
  `fresh-road/examples/tsa23_c5_network/route_fixture/`; runtime is ignored)
- Initial schedule: `runtime/ws4/schedule_baseline.csv`
- 5 years, 5 iterations, seed 1, 1 worker
- No WS4 objective, constraint, growth, or solver code changed

Command:

```bash
ws4 optimize \
  --dataset runtime/ws4/compiled_sf_risk \
  --targets config/risk_objective.yaml \
  --years 5 --iterations 5 --threads 1 --seed 1 \
  --time-limit 00:05:00 \
  --initial-schedule runtime/ws4/schedule_baseline.csv \
  --route-config config/ws4/route_c5.yaml \
  --out runtime/ws4/route_c5_opt
```

## Result

- Status: `ok`
- Blocks scheduled: 2,003
- Route product rows: 11,741
- Unrouted route rows: 0
- Route-report volume: 5,415,913.71
- First-period route length: 5,928,593.57 m
- First-period route cost: 62,832,079.26 CAD
- First-period costs: build 28,793,029.26 CAD; haul 22,389,897.25 CAD;
  maintenance 11,649,152.75 CAD
- First-period average haul: 44.855 km
- Time limit reached after the 5-iteration budget

The run used the 600 m c5 lattice, three 100 Mile House mills, and the c5
cost fields.  The DRA-only orphan components are not part of this network.

## Caveats

- Smoke run, not an optimized or converged schedule.
- Route assignment is least-haul; no product eligibility or mill demand is
  modelled.
- The four potential classes share the c5 `N` construction cost.
- The route tables are in ignored runtime storage; publish them through DataLad
  or copy them when the instance is distributed.
