# TSA23 fuel-treatment layer (design)

Status: draft
Phase: fuel-treatment layer (follow-on to P109)
Date: 2026-10-19

## Thesis formulation (from the proposal)

Optimize the **timing, placement, and intensity** of landscape-level wildfire
fuel-mitigation treatments under a budget, on the 100 Mile House TSA (TSA23),
using a forest estate model. Patchworks is the reference; WS4 is the open
delivery engine.

Decision variables: for each block and period, which fuel treatment (if any) and
at what intensity.

## Representation: FT = a re-branded commercial thinning

The fuel treatment is implemented as a **commercial thinning (CT)** with fuel
semantics, following the MKRF and K3Z CT implementations
(`femic-mkrf-instance/config/silviculture.mkrf.yaml`,
`femic-k3z-instance/config/silviculture.k3z.*.yaml`). The treatment label is
`FT` (not `CT`) so it is not confused with commercial thinning.

- `config/silviculture.tsa23.yaml` enables `commercial_thinning` with
  `label: FT`, `from_state: cc_pl` -> `to_state: cc_pl_ct` (the state name is an
  implementation detail), eligible on the 42 conifer AUs, age 40, intensity
  variants low/medium/high (basal-area removal 0.35/0.45/0.55).
- FEMIC emits `label="FT"` treatments and `...Total.FT` / `...<species>.FT`
  accounts (FEMIC PR for the configurable label: `UBC-FRESH/femic#327`).
- WS4 compiles the model with `CC` and `FT` treatments.

## Eligibility and operability (Paper 1)

Per `Jamie-Iversen-MASc-Paper-1` (the stand-level fuel-treatment decision support
flowchart), a stand is **not** fuel-treatable when any of the following holds:

- Inadequate fuel (BCLCS): <5% vegetation coverage (non-vegetated), <10% crown
  cover of any species/size (non-treed), or wetland.
- Extremely low risk: broadleaf species composition >75%, or average stand
  height <3 m.
- BEC not conducive to fire: alpine tundra (AT), bunchgrass (BG), and specific
  wet/cold subzones of BWBS, CWH, ESSF, ICH, and SBS.

Remaining stands are treatable, with the prescription (and intensity) set by
fire-weather zone, BEC, leading species, stand structure, and fuel-management
goals. In the proposal, the prescription ranges map to treatment intensities.

TSA23 application:

- BEC zones present are IDF, SBS, SBPS, MS, ESSF, ICH; AT/BG are absent, so no
  zone-level exclusion applies. (Wet/cold ESSF subzone exclusion is a refinement.)
- The broadleaf >75% exclusion maps to the **IDF_AT** analysis units, which are
  excluded from FT eligibility (FT is enabled on the 42 conifer AUs).
- Height and BCLCS exclusions are stand-level attributes not carried at the AU
  level; they are a later refinement (stand-level eligibility filter).
- **Origin is not an eligibility criterion**: FT applies to first-growth
  (natural) and planted stands alike. Implemented via
  `commercial_thinning.origins: [natural, planted]` with per-origin states
  (`UBC-FRESH/femic` multi-origin CT change), verified to emit FT on both the
  `baseline` (natural) and `cc_pl` (planted) tracks.

## Economics (BC programme evidence)

- **Treatment cost: $10,000/ha.** Charged per treated hectare when FT is applied.
  Anchored on BC Forest Practices Board FPB/SIR/43 (2015, p. 18): the average fuel
  management treatment under the Strategic Wildfire Prevention Initiative was about
  $10,000/ha, unchanged 2009–2014. Full assumptions and sources: `config/costs.yaml`.
- **Fuel break (FB) disposal: $7,500/ha.** The FNESS 2024/25 Cariboo Fire Centre
  operational allowance (TSA23 is in the Cariboo Fire Centre). The merchantable
  clearcut FB contains is why its net subsidy sits below the gross thinning average.
- **Surface fuel (SF): $3,750/ha.** The FNESS maintenance allowance.
- **Small-log commercial output**: merchantable volume from the removal,
  resolved through the BTC `log-grades` indicator bank (low grades).
- **Woody biomass product**: fuel collected during the treatment, expressed as a
  biomass product.
- **Variants**:
  - FT **without** in-block chipping: yields the woody-biomass product.
  - FT **with** in-block chipping: the low-grade biomass product goes away
    (chipped in block) but at an **extra cost**.

## Mapping to the stack

| Element | Where | Mechanism |
| --- | --- | --- |
| FT treatment + state transition | FEMIC export | `commercial_thinning` in `config/silviculture.tsa23.yaml`, `label: FT` |
| Small-log product | FEMIC/BTC | `btc_indicator_banks: [log-grades]` (export-supported) |
| Woody-biomass product | FEMIC/BTC | BTC `biomass-live` / `residual-fibre` banks (build-stage; not yet in the export allow-list) |
| Treatment cost ($10k/ha) | FEMIC/instance economics | area cost applied to the FT treatment (MKRF pattern: `harvest_costs.*.yaml`); source in `config/costs.yaml` |
| Chipping variant | config + products | separate FT variant; removes biomass product, adds cost |
| Budget constraint | WS4 | a level target with a `maximum` on the FT cost account, per period |
| Objective | WS4 | a target on a fire-metric account (to be defined from Chapter 1 curves) |

## Gaps / next steps

1. **Cost wiring**: `harvest_costs`/`log_grade_prices` are instance-level in MKRF,
   not core FEMIC. Decide whether TSA23 grows the same instance economics layer
   or whether a core FEMIC cost surface is added.
2. **Biomass product**: the export's `btc_indicator_banks` allow-list is
   `log-grades` and `stand-structure-basic`; biomass banks exist in
   `femic/pipeline/tipsy.py` but are not wired to the export. Needs either a
   rebuild with the biomass banks or an export allow-list extension.
3. **Chipping variants**: represent as two FT treatments (or an intensity/bank
   variant) with different cost and product sets.
4. **Fire-metric accounts**: define the hazard/benefit curves per AU (Chapter 1
   treatment curves) so WS4 has an objective to minimize.
5. **Budget + objective study**: assemble the WS4 targets and run the
   optimization for TSA23.
