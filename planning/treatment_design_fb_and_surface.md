# Treatment design: fuel break (FB) and surface-fuel reduction (SF)

Status: design accepted, implementation starting
Date: 2026-10-19
Companions: `planning/fuel_treatment_layer.md`, `planning/paper2_modelling_plan.md`,
`planning/paper2_evidence_log.md`

## Decision

Add a **distinct fuel-break treatment (FB)** — a clearcut **plus full post-harvest
fuel disposal** — and, after it, **surface-fuel reduction (SF)** as a distinct
treatment the scheduler can sequence. Do **not** implement FB as a fourth
thinning intensity.

## Treatment taxonomy

| label | operation | state | post-treatment fuel hazard |
| --- | --- | --- | --- |
| `CC` | clearcut, slash left | harvested/regenerating | **spike** (activity fuels), then recovery |
| `FT` | thinning (3 intensities: BA removal 0.35/0.45/0.55) | stand remains | reduced crown fire, then recovery |
| `FB` | clearcut **+ full fuel disposal** (chip/burn/masticate/remove) | harvested/regenerating | **near-null** for N years, then recovery |
| `SF` | surface-fuel reduction | stand remains | reduced surface ROS, window-limited |
| none | no treatment | unchanged | unchanged |

## Why FB is distinct, not intensity #4

A thinning intensity is a *removal fraction* on the same state track (stand
remains, residual curve). FB:

- **removes the stand and resets age** (a new state, like `CC`);
- has a different **product/cost profile** (full merchantable volume + cleanup cost);
- has a different **post-treatment fuel trajectory** (near-null, then regrowth);
- has different **eligibility/operability**.

Collapsing it into the intensity axis would conflate "how much basal area removed"
with "stand removed", and the scheduler could not distinguish them.

## A clearcut is not a fuel break

A clearcut leaves slash and activity fuels — often **more** flammable for several
years. The near-null state exists only if the harvest includes **full disposal**.
So model `CC` (no cleanup, hazard spike) and `FB` (cleanup, near-null) as the
contrast. "Fuel break" is a treatment package, not a harvest method; this is a
result in its own right.

## Hazard (treatment) curves

Each treatment needs a post-treatment fire-metric trajectory, per AU (the Paper 1
"treatment curves", linked to FBP):

- `FB`: near-null for **N** years (provisional N = 5-10), then rise with regrowth
  to the AU's fuel-type hazard.
- `CC`: **above** baseline for the slash years, then recovery.
- `FT`: reduced crown-fire potential (CFB) for the residual period, then recovery.
- `SF`: reduced surface ROS for its window, then recovery.

The curve should be a single auditable **hazard index** (0-1) per track, from
which the spread model derives a spread-rate multiplier; ROS/HFI/CFB from FBP
remain the diagnostics.

## Surface-fuel reduction: sequential, not a combo

- Implement `SF` as a **distinct treatment** on the post-thinning track
  (`cc_pl_ct`), with an **age window** = the operability window after thinning
  (e.g., 0-10 years).
- This lets the scheduler choose *whether and when* to follow up, preserves the
  thesis's timing dimension, and avoids conflating two operations with different
  costs/effects.
- A bundled "combo" is the fallback if sequencing proves too slow for the search.

## Mapping to the stack

| element | FEMIC | WS4 |
| --- | --- | --- |
| `FB` treatment | a `CC`-like treatment with a dispose flag + cost | a treatment with a transition to a cleaned state |
| post-treatment hazard | a feature curve per AU/state | a feature (`feature.FuelHazard`) with a curve |
| `SF` treatment | a treatment on the thinned state with an age window | a treatment with `begin/end` on the post-thinning track |
| cost/products | per-treatment economics (instance layer) | product/cost accounts |
| spatial benefit | — | connectivity/patch accounts (the bridge) |

## Implementation plan

1. **This note.**
2. Add a per-track **hazard** feature to the model (near-null / reduced / spike /
   baseline curves per state).
3. Add **`FB`** as a `CC`-like treatment with disposal, cost, and the near-null
   hazard curve.
4. Add **`SF`** as a post-thinning treatment with an age-window operability.
5. Make the spread model consume the hazard (spread multiplier) instead of a flat
   `--treat-ros-factor`.
6. Re-run **E2c** with `FB` as the real hard break; the arrangement effect should
   be the hard-break result (~5-6%), now driven by the model rather than a flag.

## Open questions

- `N` (near-null duration) and the cleanup cost; products under disposal
  (biomass vs chipped).
- The hazard metric definition and its FBP link.
- Whether `FB` is areal or linear; the scheduler's pattern (linear breaks) is a
  target/account choice, not a treatment property.
