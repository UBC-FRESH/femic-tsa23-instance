# TSA 23 road-aware optimization attempt

Date: 2026-10-29

This records an unsuccessful road-aware optimization attempt.  It is not a
model result.

## What was tried

1. Full c5 network with `initial_roads: existing` (potential roads built on
   demand).
2. A reduced candidate network containing existing roads plus the potential
   segments used by the existing `risk_opt_final` schedule.

## Findings

- Full c5 network, 10-block simulation with `initial_roads: existing`:
  **100 seconds**.  A 2,000-block schedule would be hours, so the full
  465k-segment network is not viable for optimizer iterations as-is.
- Reduced network: 43,250 segments (38,947 existing + 4,303 potential used by
  the current schedule); 714-block simulation took **132 seconds**.
- A one-iteration optimizer run on the reduced network scheduled 2,001 blocks
  but produced **7,587 unrouted route product rows**.  The reduced network is
  not connected for schedules that use blocks outside the original used-road
  set, so it is not a valid road-aware optimization fixture.

## Decision

Do not use the reduced candidate network for optimization.  The valid result
remains the report-only c5 route accounting on `risk_opt_final`:

- 714 blocks
- 0 unrouted route rows
- 11.23 M build, 60.89 M haul, 4.56 M maintenance, 76.68 M total

Road-aware optimization needs either:

- a performance strategy for the full connected c5 network, or
- a separate network-design formulation that preserves connectivity while
  reducing candidate edges.

No objective, constraint, growth, or solver code was changed.
