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

**RQ2 — the value.** Under which fire-weather conditions and at which **treated
area** do fuel treatments reduce landscape fire behaviour, and how much of the
benefit is **arrangement** (pattern / orientation) versus treated area?

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
barrier patterns through the spread model. *Status: done, conditional.* At **20%
treated, p90**, barrier < clumped < random (19,640 / 19,870 / 20,298 ha mean
burned), a ~3% spread. This is a **benchmark at a fifth of the landscape**, not a
universal arrangement result: the effect depends on weather and on how close the
treatment is to a hard break (E2c/E9/E10). At the **feasible ~5.5% footprint** in
the matched-footprint test the five-seed mean ranking reverses and the mean gap
(86 ha, 0.38%) is inside the seed range (~3,400 ha, 15%); see E7 and #14.

**E3 — the bridge oracle.** Do WS4 spatial accounts reproduce the E2 ranking?
*Status: done, negative.* Patch size ranks the barrier **worst** (largest 400+ ha
share) where fire ranks it best, so the accounts need **connectivity**, not size.
This is the measured ceiling that defines the WS4 extension.

**E4 — the decision.** With the connectivity account, does scheduling against it
change placement/timing versus area+cost alone? *Status: deferred as a
decision-sensitivity experiment, not a bridge validation.* The account exists
(E12) and the optimizer can target it, but #14 established that at the feasible
footprint the account is not a validated fire-response proxy. Running E4 would
measure the decision effect of a fragmentation metric; it cannot restore the
fire claim. The paper's conditional/negative framing does not depend on E4.

## Treatment coverage (E5)

The proposal names eight treatment types; the WS4 prototype implements **thinning
only** (`FT`, three intensities). The E2c result shows the spatial benefit depends
on the treatment's effect on spread, so the treatment space must be widened to the
**three mechanisms**: crown (thinning), surface (burning/mastication), and break
(clearcut + disposal). Design: `planning/treatment_design_fb_and_surface.md`.

- [ ] **FB** — a distinct clearcut **+ full fuel disposal** treatment with a
      near-null hazard for N years, then recovery (not a fourth thinning intensity;
      a clearcut alone leaves slash and is not a break).
- [ ] **SF** — surface-fuel reduction as a distinct post-thinning treatment with an
      age-window operability (sequential, not a bundled combo).
- [ ] A per-track **hazard feature** the spread model consumes (replacing the flat
      `--treat-ros-factor` stand-in).
- [ ] Re-run **E2c/E3** with FB as the real hard break.

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

## Framing decision (closed #14)

The paper does **not** claim a universal arrangement effect. It reports three
things, in this order:

1. **The 20% benchmark is conditional.** At 17.9% of the fire model, p90 weather,
   barrier < clumped < random, a ~3% mean spread. E2b/E2c/E9/E10 narrow it: the
   ordering depends on the fire-weather scenario and on whether the treatment is a
   soft slowdown or a near-hard break. At median weather the barrier is the worst
   arrangement; above p85 it is best. It is a benchmark for "what arrangement can
   do when a fifth of the landscape is treated", not a claim about an estate plan.
2. **The feasible-estate answer is negative at current treatment levels.** At the
   ~5.5% footprint WS4's FT can deliver, the five-seed means reverse and the mean
   gap is 0.38%, well inside the ~15% seed range. A planning model cannot use this
   fire model to choose an arrangement at that treatment level.
3. **The compartment account is a correct metric, not a validated fire proxy.**
   E12 verifies its values against an independent implementation, but E7/P16.1
   show it does not track the fire outcome at the matched footprint. The bridge
   validation is withdrawn; the account remains a targetable fragmentation metric.

If the student chooses the 20% result as the paper's headline, the title, abstract
and E2 must name **17.9% treated, p90 weather, and the near-hard treatment factor**.
If the student chooses the estate-model question, the headline is the **negative**
result and the 20% case is the upper-bound benchmark. The plan of record is the
second framing with the first reported as a conditional benchmark; either way, no
sentence may say "arrangement matters" without the treated fraction and weather.

## Deliverables and sequencing

- **Paper 1** (Jamie's, the stand-level flowchart / decision-support guide) —
  separate; supplies the treatment logic the model consumes.
- **Paper 2** (this): the landscape model. Sequence: E1, E2 (done) → the WS4
  connectivity account → E3 oracle → the #14 framing decision → write-up. E4 is
  deferred as a decision-sensitivity experiment, not a bridge validation.
- **WS4 extensions**: the connectivity/compartment account (prompt drafted); the
  optimizer seed (done: `--seed-greedy`).

## Honest uncertainties

- The spatial effect is **conditional**: ~3% at the 20% p90 benchmark, inside noise at the
  ~5.5% feasible footprint, and weather-dependent. The paper reports both; it does not
  generalise from the 20% case.
- The spread model is a **simplification** (no suppression, isotropic within a
  block, a flat treated-ROS factor standing in for crown-fire prevention). It
  needs a stronger, literature-grounded fire model before the numbers are quoted.
- If the bridge **fails**, contribution (1) becomes a negative result; that is
  still a contribution (the lab's parity work treats measured ceilings as
  findings), but the thesis would lean on (3) instead.
- The **FT area account** in WS4 reads 4× hectares (see the WS4 finding), so any
  area target must be placed on the cost account until that is fixed.
