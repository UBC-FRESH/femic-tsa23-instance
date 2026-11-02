# TSA 23 target semantics under WS4 P86

Date: 2026-11-02
Status: interpretation of an existing result; no new run, target, or model change.

## Purpose

The TSA 23 road-aware optimizer run did not meet its 10,000,000 CAD route-build
target. This note records the WS4 P86 interpretation so that the miss is read as
a goal-programming result, not as a solver defect.

Reference result: `reports/ws4-road-aware-opt.md`.

## The target set

`config/ws4/risk_road_objective.yaml` carries five one-sided targets:

| Account | Period | Bound | Weight |
| --- | ---: | ---: | ---: |
| `feature.RiskWeightedHazard` | 4 | maximum 21,582 | 1.0 |
| `product.FuelTreatmentCost` | 4 | maximum 50,000,000 | 10.0 |
| `product.FuelBreakCost` | 4 | maximum 25,000,000 | 10.0 |
| `product.SurfaceFuelCost` | 4 | maximum 25,000,000 | 10.0 |
| `route.Total.build` | 1 | maximum 10,000,000 | 1.0 |

The 10,000,000 CAD route-build value is a benchmark scenario bound, not a policy
recommendation.

## P86 interpretation

WS4 P86 documents weighted goal programming: a minimum or maximum is a one-sided
penalty hinge, not a hard feasibility bound. The weight controls how strongly the
search pulls toward that hinge. A `1e9` priority tier is near-lexicographic; ordinary
weights are softer.

In this target set, the three fuel-cost targets carry weight 10.0, while hazard and
route build carry weight 1.0. The search therefore gives fuel cost first claim on
the trade-off, then hazard and route build. The observed result is consistent with
that design:

- 100 iterations, 2,031 blocks, 0 unrouted route rows;
- `route.Total.build` 27,409,188.40 CAD against the 10,000,000 CAD aspiration;
- `feature.RiskWeightedHazard` 21,965.48 against the 21,582 maximum;
- fuel-cost and route accounts remain explicit.

The build target is unmet because it is a soft, lower-weight aspiration and the
solver found a schedule that spends more road capital to reduce fuel-treatment cost
and hazard. The run does not show that 10,000,000 CAD is infeasible.

## Consequence

- Do not describe the 10,000,000 CAD miss as a solver failure.
- If 10,000,000 CAD is a real budget, make it a hard constraint or raise its weight
  in a separately reviewed scenario.
- If it is an aspiration, report the build/hazard/fuel trade-off and the weight
  choice explicitly.
- Do not change the target file as part of this note; this is an interpretation only.

## Forest-condition card

`reports/tsa23-forest-condition-2026.json` and `.md` publish the BA-only inventory
pilot as a `ws4.forest_condition.report.v1` card. It carries the 23.87 m2/ha BA
indicator, the 8.86 m2/ha strict independent RMSE, the 14.9% coverage applicability,
and an advisory coverage alert. The card is `draft` and report-only; it is not an
operational early-warning product and does not change the model.
