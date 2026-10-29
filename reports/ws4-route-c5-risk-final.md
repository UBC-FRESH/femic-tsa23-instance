# TSA 23 c5 route accounting on the risk-optimized schedule

Date: 2026-10-29

This applies the planned c5 road network to the existing `risk_opt_final`
schedule.  It is report-only: no objective, constraint, growth, or solver code
is changed.

## Configuration

- Dataset: `runtime/ws4/compiled_sf_risk`
- Schedule: `runtime/ws4/risk_opt_final/schedule.csv`
- Route config: `config/ws4/route_c5.yaml`
- Route tables: `runtime/ws4/roads_c5/`
- 5 years

Command:

```bash
ws4 simulate \
  --dataset runtime/ws4/compiled_sf_risk \
  --schedule runtime/ws4/risk_opt_final/schedule.csv \
  --years 5 \
  --route-config config/ws4/route_c5.yaml \
  --out runtime/ws4/risk_opt_final_c5
```

## Result

- Blocks: 714
- Route product rows: 5,883
- Unrouted route rows: **0**
- Route-report volume: 15,169,247.32
- Route length: 2,340,222.46 m
- Build expense: 11,230,795.19 CAD
- Haul expense: 60,889,150.97 CAD
- Maintenance expense: 4,558,614.24 CAD
- Total route expense: 76,678,560.40 CAD
- Average haul: 43.641 km

Destination split by ledger volume:

| Destination | Volume | Haul expense (CAD) |
|---|---:|---:|
| `destination.MILL_733_LGH` | 8,998,034.14 | 37,090,926.86 |
| `destination.MILL_95_LBR` | 5,000,360.43 | 20,963,627.36 |
| `destination.MILL_694_LGH` | 1,170,852.75 | 2,834,596.74 |

The common product accounts in `risk_opt_final` and this route run are
**identical** (973 accounts, max absolute delta 0.0). The route accounts are
additive only.

## Caveats

- This is a report-only accounting run against an existing schedule; it is not
  a road-aware optimization.
- Route assignment is least-haul; no product eligibility or mill demand is
  modelled.
- The four potential classes share the c5 `N` construction cost.
- Route tables remain in ignored runtime storage; publish them through DataLad
  or copy them with the instance.
