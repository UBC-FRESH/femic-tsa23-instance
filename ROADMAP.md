# TSA23 Instance Roadmap

## Phase 0: Bootstrap (P108 — P108.2–P108.5)

- [x] Create `UBC-FRESH/femic-tsa23-instance` public repository (parent #302, child #298)
- [x] Add parent submodule under `external/femic-tsa23-instance` (child #298)
- [x] Bootstrap instance governance, structure, and package scaffold (child #299)
- [x] Plan TSA23 source workflow and first build phases (child #300)
- [x] Write delegated result report and open P108 PR (child #301)

## Phase 1: Source/Corpus Discovery and Materialization

Parent issue: #1
Branch: `feature/p109-source-discovery-materialization`
Status: pr-open

Goal: materialize the TSA23 source layers and instance configuration, and prove
the instance builds end-to-end (TSR -> sources -> FEMIC build -> Patchworks
export -> WS4 build/simulate).

- [x] P109.1 TSR fetch, candidate-fact review, and reviewed overlay (#2)
  - [x] `femic tsr fetch --tsa 23` (18/18 PDFs cached)
  - [x] `femic tsr facts-report --tsa 23` review of source-layer/THLB candidates
  - [x] `config/tsr/overlay.yaml` with 17 adopted source layers (`proposed`)
- [x] P109.2 Source-layer materialization (VRI/SiteProd/TSA boundary) (#3)
  - [x] Arbutus `arbutus-s3` special remote enabled
  - [x] VRI 2024/2025, SiteProd, and TSA boundary materialized
- [x] P109.3 Instance configuration and provisional TIPSY rules (#4)
  - [x] `config/run_profile.tsa23.yaml`, `config/seral.tsa23.yaml`, `config/vdyp_fit_policy.yaml`
  - [x] `config/rebuild.spec.yaml` (canonical), `config/tipsy/tsa23.yaml` (provisional)
- [x] P109.4 First end-to-end build and WS4 validation (#5)
  - [x] `femic run --tsa 23` (45 AUs; VDYP curves under Wine)
  - [x] `femic export patchworks --tsa 23` (`forestmodel.xml` + `fragments.shp`)
  - [x] `ws4 build` + `ws4 simulate` (100-year run)

Deferred to a later phase: the BatchTIPSY handoff (managed/treated curves), the
wildfire fuel-treatment optimization layer, and per-AU TIPSY refinement.

## Phase 2: TSR/THLB Interpretation (P110 — tentative)

- [ ] Fetch and index TSA23 TSR documents via FEMIC TSR surfaces
- [ ] Extract candidate facts; initialize reviewed overlay
- [ ] Inspect adopted-vs-canonical TSR state for TSA23
- [ ] Document THLB/THNS boundaries and definitions as taught in the source

## Phase 3: Source-Layer and Inventory Materialization (P111 — tentative)

- [ ] Validate boundary geometry against parent reviewed TSA
- [ ] Run SiteProd assignment (canonical artifacts preferred; ArcRasterRescue fallback)
- [ ] Execute VDYP run for TSA23 plots/stands
- [ ] Build curve tables and AU assignment (`scsi_au`, `au_scsi`)
- [ ] Generate BatchTIPSY handoff files

## Phase 4: Model-Design Assumptions (P112 — tentative)

- [ ] Define seral trajectory assumptions for TSA23
- [ ] Select treatment states and CC age rules
- [ ] Choose curve-source mapping (untreated/treated origin vs managed/unmanaged)
- [ ] Document all model-design defaults in assumption registry

## Phase 5: Model-Input Bundle Generation (P113 — tentative)

- [ ] Generate `forestmodel.xml` via FEMIC exporter
- [ ] Build fragments shapefile/DBF with correct attributes
- [ ] Assemble Patchworks runtime package (`tracks/`, `blocks/`)
- [ ] Validate inputs against Matrix Builder requirements

## Phase 6: Patchworks Runtime Package (P114 — tentative)

- [ ] Run Patchworks Matrix Builder for TSA23 baseline
- [ ] Inspect outputs: `features.csv`, `protoaccounts.csv`, `accounts.csv`
- [ ] Verify species-share sanity (zero source share ≠ zero runtime signal)
- [ ] Run scenario models as defined

## Phase 7: Publication/Teaching Docs (P115 — tentative)

- [ ] Build Sphinx docs with TSR-style depth matching other TSA instances
- [ ] Add area accounting, THLB/AU documentation, seral interpretation guides
- [ ] Add operator runbooks and troubleshooting guidance
- [ ] Validate Sphinx docs build (`sphinx-build -b html docs _build/html -W`)

## Phase 8: FreshForge Materialization/Workflow (P116 — tentative)

- [ ] Define FreshForge workflow graphs for TSA23 rebuild automation
- [ ] Document checkpoint/resume strategy
- [ ] Validate automated full rebuild from source layers to Patchworks output

## Phase 9: Sphinx Docs Site and Publication (P117)

Parent issue: #15
Branch: `feature/p117-sphinx-docs`
Status: planned
Plan: `planning/sphinx_docs_plan.md`

Goal: build and publish the instance documentation with the
`UBC-FRESH/ubc-fresh-dev-workflow` docs workflow — `sphinx-build -W` in CI, deployed
to GitHub Pages — so the site is the project's RTFM surface and agents cite it.

- [ ] P117.1 Align the build with the template: `docs/requirements.txt`, `conf.py`,
      `index.rst`, `api/`, `llms.txt`
- [ ] P117.2 Add `.github/workflows/docs.yml`: build with `-W`, upload the Pages
      artifact, deploy from `main`
- [ ] P117.3 Enable Pages (source: GitHub Actions) and verify the first deploy
- [ ] P117.4 Content pass: keep the operator pages, add API pages for the scripts,
      link public-safe runbooks and planning notes
- [ ] P117.5 Public-safety pass on everything the site publishes

Acceptance criteria:

- `sphinx-build -b html docs _build/html -W` succeeds from a clean checkout with only
  `docs/requirements.txt` installed.
- The Pages URL serves the site and `llms.txt` is reachable.
- The API reference renders real docstrings, not a placeholder page.
- The workflow is the only build path; the dashboard/CI state is green on `main`.

Note: this is the site infrastructure. The Phase 7 (P115) content programme fills it;
P117 is complete when the surface builds and publishes, not when it is exhaustive.

