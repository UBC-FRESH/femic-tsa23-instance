# Change Log

## 2026-10-20 — Working instance, corrected datasets, published docs

- `requirements.txt` replaced the submodule placeholder with the real analysis stack;
  `cffdrs` is pinned to a git commit because it is not on PyPI.
- `docs/quickstart.rst` rewritten for the standalone repository: clone, venv, data
  bundle, verification, first analysis. The submodule/PowerShell path was stale.
- `runbooks/data-bundle.md` records what a working checkout needs and how to ship it
  (72 MB compressed, 175 MB unpacked).
- WS4 datasets recompiled without duplicate product rows; the FB/SF builders no longer
  collapse rows that differ only by treatment.
- `docs/rebuild-contract.rst` now separates the two meanings of "build": the released
data bundle (what a clone can do) and the from-source rebuild (which needs the external
BC layers plus Wine and Patchworks, and cannot run from this tree).
- Sphinx site published at https://ubc-fresh.github.io/femic-tsa23-instance/, built by
  the lab template's Pages workflow.


## 2026-07-05 — P108 Bootstrap

- Created `UBC-FRESH/femic-tsa23-instance` public repository.
- Added as submodule under parent FEMIC `external/femic-tsa23-instance`.
- Bootstrapped instance governance surfaces:
  - `README.md` — project overview, quick start, rebuild contract summary.
  - `AGENTS.md` — agent operating notes adapted from parent FEMIC conventions.
  - `ROADMAP.md` — phased roadmap from P108 bootstrap through P116 FreshForge workflow.
  - `CHANGE_LOG.md` — this file.
- Initialized directory structure:
  - `config/` — rebuild spec, TSR overlay, tipsy config placeholders.
  - `docs/` — Sphinx scaffold (conf.py, index.rst).
  - `runbooks/` — operator runbook templates.
  - `workflows/freshforge/` — FreshForge workflow graph definitions.
  - `planning/` — phase planning notes.
- Record of reference borrowing:
  - Structure/layout copied from `femic-tsa29-instance`.
  - Issue/roadmap discipline adapted from `femic-tfl6-instance`.
  - All modelling assumptions deferred to P109+; no TSA23-specific data tracked yet.

## 2026-07-08 - Reconciled P108 bootstrap roadmap status

- Updated `ROADMAP.md` Phase 0 to mark P108.4 and P108.5 complete after parent
  FEMIC issues #300 and #301 were verified closed.
- Extended the Phase 0 range from P108.2-P108.4 to P108.2-P108.5 so the
  instance roadmap matches the parent P108 bootstrap completion state.

## 2026-10-18 — P109 Source discovery and first materialization

- TSR discovery: `femic tsr fetch --tsa 23` cached 18/18 TSA23 TSR PDFs;
  `femic tsr facts-report --tsa 23` reviewed source-layer and THLB candidates
  (17 likely-useful source layers, all from the TSR 2012 Data Package).
  `femic tsr overlay-init` produced `config/tsr/overlay.yaml` with 17 adopted
  source layers (`status: proposed`).
- Source materialization: enabled the Arbutus `arbutus-s3` DataLad remote and
  materialized VRI 2024/2025, SiteProd, and the TSA boundary. VRI 2025 is the
  FEMIC-selected vintage; species composition lives in `SPECIES_CD_1..6` /
  `SPECIES_PCT_1..6` for treed polygons (`BCLCS_LEVEL_2 = 'T'`).
- Instance configuration: added `config/run_profile.tsa23.yaml`,
  `config/seral.tsa23.yaml`, `config/vdyp_fit_policy.yaml`, the canonical
  `config/rebuild.spec.yaml`, and `config/tipsy/tsa23.yaml`. The TIPSY rules are
  per-(leading-species, SI-level) from TSR 2012 Table 21 (regeneration
  assumptions) and Table 22 (genetic worth of non-pine seedlings, columns
  Fdi/Sx/Pli), with FEMIC's L/M/H mapped to TSR poor/medium/good; OAF follows
  Section 6.2.3 (OAF1 auto-derived, OAF2 0.95).
- End-to-end build: `femic run --tsa 23` completed (45 AUs; VDYP7 7.16k under
  Wine). `femic export patchworks --tsa 23` wrote `forestmodel.xml` and
  `fragments.shp` (45 AUs, 102,128 fragments, 136 curves). `ws4 build` and a
  100-year `ws4 simulate` completed on the exported model (168,405 blocks;
  1,037,011 m3 harvested in year 0).
- Managed lane: BatchTIPSY (BTC) was executed on this Linux host under Wine.
  A `xvfb-run wine TIPSYbtc.exe` wrapper was set as `FEMIC_BATCHTIPSY_EXE`
  (wine-mono installed into the prefix), and `femic tipsy run-btc
  data/03_input-tsa23.csv --mode TSR` produced `data/04_output-tsa23.csv`
  (exit 0). `femic tsa post-tipsy --tsa 23` then rebuilt the bundle with
  treated/managed curves (45 AUs, 3,150 curves, 18,041 curve points). Re-export
  and a WS4 build + 100-year simulate ran green; year-0 harvest rose from
  1,037,011 m3 (untreated only) to 1,314,252 m3 with managed curves included.
- FEMIC defects found during the build (to be filed upstream): `pandas<3` pin,
  `plots/` directory not created before `savefig`, `assign_siteprod_from_raster`
  fails on an empty frame, and `--debug-rows` subsets the province-wide VRI
  before TSA/treed filtering.
- Formalized Phase 1 as parent issue #1 with child issues #2-#5 on branch
  `feature/p109-source-discovery-materialization`.
