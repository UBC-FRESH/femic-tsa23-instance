# Paper 2 modelling plan

Status: draft
Phase: Paper 2 (landscape fuel-treatment modelling)
Date: 2026-10-19
Companions: `planning/fuel_treatment_layer.md`, `planning/paper2_fire_behaviour_bridge.md`,
`planning/paper2_evidence_log.md` (all numbers, commands, caveats)

## Purpose

Fix what Paper 2 *is*: its research questions, the model chain, the experiments,
the contributions, and the deliverables — and ground each in the literature. The
goal is to turn "we have a working model" into "here is what the model is a
vehicle for".

## Research questions

**RQ1 — the bridge.** Can a *strategic forest estate model* carry a landscape
fire-spread response as **native spatial accounts** (patch and connectivity), so
a treatment schedule can be optimized against it inside the estate model?

**RQ2 — the value.** Under which fire-weather conditions do fuel treatments
reduce landscape fire behaviour, and how much of the benefit is **arrangement**
(pattern / orientation) versus **treated area**?

**RQ3 — the decision.** Does optimizing against the spatial fire accounts change
the **treatment decision** (placement, timing) versus optimizing against area and
cost alone?

## The model chain

```
BC VRI + TSR  --FEMIC-->  TSA23 model (curves, strata/AUs, FT treatments)
                               |
                               v
                         Patchworks export --> WS4 (schedule, budget, spatial accounts)
                               |                     ^
                               v                     |
                    FBP stand-scale curves -->   the bridge  <-- network spread model
                    (ROS/HFI/CFB, untreated vs      (compile pattern->outcome
                     thinned, by weather)            into patch/connectivity accounts)
```

- **FEMIC** builds the 100 Mile House (TSA23) model: VRI, TSR-informed silviculture,
  yield curves, and the fuel treatment **FT** (a re-branded commercial thinning).
- **WS4** is the estate model: schedules FT and harvest over time under a budget,
  with spatial accounts.
- **FBP** (`cffdrs`) gives the stand-scale treatment effect: crown fraction burned
  and head-fire intensity fall with thinning, weather-conditionally.
- The **network spread model** turns a fuel pattern into a landscape outcome
  (area burned, burn probability).
- The **bridge** is the contribution: compile that response into WS4's spatial
  accounts so the estate model can *see* it.

## Experiments

**E1 — weather-conditional treatment value.** FBP per AU, untreated vs thinned,
under median / p90 / extreme fire weather (ERA5-derived FWI). *Status: done.*
Result: treatments cut crown fire and intensity under median weather (C3 CFB
0.11→0.00) but are overwhelmed at p90/extreme (CFB ≈ 1.0). The benefit is
weather-conditional.

**E2 — pattern / orientation.** Equal-area random / clumped / wind-perpendicular
barrier patterns through the spread model. *Status: done.* Result: barrier <
clumped < random (20% treated: 19,640 / 19,870 / 20,298 ha mean burned); the
arrangement effect grows with crown-fire suppression (~3% at 20%).

**E3 — the bridge oracle.** Do WS4 spatial accounts reproduce the E2 ranking?
*Status: done, negative.* Patch size ranks the barrier **worst** (largest 400+ ha
share) where fire ranks it best, so the accounts need **connectivity**, not size.
This is the measured ceiling that defines the WS4 extension.

**E4 — the decision.** With the connectivity account, does scheduling against it
change placement/timing versus area+cost alone? *Status: pending the account.*

## Contributions (grounded in the literature)

The field — Yemshanov et al. (network fuel-break optimization; critical-edge
removal; compartmentalization), Nguyen et al. (MIP fuel-treatment prioritization),
Nicoletta et al. (burn-probability + loss + network optimization), Dent et al.
(graph partitioning) — optimizes fuel breaks/treatments **as a network problem,
separately from the timber-supply estate model**. Başkent et al.'s review flags
the integration of spatial risk into planning as under-developed.

1. **The bridge (highest odds).** Carry the network fire-spread response inside a
   strategic estate model as **native spatial accounts** (connectivity /
   compartmentalization), demonstrated on a real BC TSA. If it works, it is the
   contribution; if it fails, the measured ceiling is the finding.
2. **Joint scheduling (moderate).** Timber supply + fuel treatment + budget +
   spatial pattern in **one** model, rather than a separate network problem.
3. **Weather-conditional value (a result, moderate).** The treatment benefit is
   weather-conditional; arrangement's contribution scales with crown-fire
   suppression.
4. **BC case study (low novelty alone, needed as context).** 100 Mile House TSA,
   FBP + TSR.
5. **Cost-benefit under budget (necessary, low novelty).** The thesis's stated
   core.

## Deliverables and sequencing

- **Paper 1** (Jamie's, the stand-level flowchart / decision-support guide) —
  separate; supplies the treatment logic the model consumes.
- **Paper 2** (this): the landscape model. Sequence: E1, E2 (done) → the WS4
  connectivity account → E3 oracle → E4 decision comparison → write-up.
- **WS4 extensions**: the connectivity/compartment account (prompt drafted); the
  optimizer seed (done: `--seed-greedy`).

## Honest uncertainties

- The spatial effect is **small (~3%)** in the current model; it may not survive a
  stronger fire model, or may be dwarfed by treated area. E2/E4 must say so.
- The spread model is a **simplification** (no suppression, isotropic within a
  block, a flat treated-ROS factor standing in for crown-fire prevention). It
  needs a stronger, literature-grounded fire model before the numbers are quoted.
- If the bridge **fails**, contribution (1) becomes a negative result; that is
  still a contribution (the lab's parity work treats measured ceilings as
  findings), but the thesis would lean on (3) instead.
- The **FT area account** in WS4 reads 4× hectares (see the WS4 finding), so any
  area target must be placed on the cost account until that is fixed.
