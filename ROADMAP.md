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
Status: active

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

Note (2026-10-20): P109.2 and P109.3 were completed at build time, but the source layers
are **not** materialized in the current tree — `femic prep validate-case` fails without
`FEMIC_EXTERNAL_DATA_ROOT`. They are reopened as `#3` and `#4` until the layers are
restored or the derived-data-only position is adopted in `docs/rebuild-contract.rst`.
P109.1 and P109.4 were re-verified and closed on 2026-10-20.

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
Branch: merged to `main` (PR #17)
Status: complete
Plan: `planning/sphinx_docs_plan.md`

Goal: build and publish the instance documentation with the
`UBC-FRESH/ubc-fresh-dev-workflow` docs workflow — `sphinx-build -W` in CI, deployed
to GitHub Pages — so the site is the project's RTFM surface and agents cite it.

- [x] P117.1 Align the build with the template: `docs/requirements.txt`, `conf.py`,
      `index.rst`, `api/`, `llms.txt`
- [x] P117.2 Add `.github/workflows/docs.yml`: build with `-W`, upload the Pages
      artifact, deploy from `main`
- [x] P117.3 Enable Pages (source: GitHub Actions) and verify a deploy —
      `https://ubc-fresh.github.io/femic-tsa23-instance/` served from the feature
      branch on a widened environment policy, then the policy was restored to `main`
- [ ] P117.4 Content pass: deferred to P115. The API pages are generated; the operator
      pages still need the P115 depth (area accounting, THLB/AU, seral guides)
- [x] P117.5 Public-safety pass on the published pages

Note: the site deploys from `main` — workflow run 39459197168 built and published it
after the merge to `main` (PR #17). The documentation infrastructure is complete; the
editorial depth is P115's, which is why P117.4 is deferred rather than done.


## Phase 10: Target semantics and forest-condition card

Parent issue: #49
Branch: `feature/p123-target-semantics-condition-card`
Status: complete

Goal: record the WS4 P86 interpretation of the road-aware target and publish a
report-only forest-condition card for the BA-only inventory pilot, without changing
the model, data, targets, or solver.

- [x] P123.1 Record P86 semantics and publish the forest-condition card (#50)
  - [x] Write the P86 target-semantics note.
  - [x] Publish the JSON and Markdown forest-condition card.
  - [x] Add the card validation test.
  - [x] Update the roadmap and changelog.
  - [x] Queue the phase pull request.

Acceptance criteria:

- The note treats the 10,000,000 CAD route-build bound as a soft aspiration, not a
  solver failure.
- The card carries a review status, source, version, applicability, uncertainty, and
  an advisory alert; it is report-only.
- The local test rejects a missing source, a non-finite value, and an invalid review
  status.
- No model, data, target, or solver value changes.

Note: the card carries only the BA-only inventory indicator. The instance has no
TSA 23 DHI calculation or source, so the DHI fixture from the separate WS4 P90
example is not copied here.

## Phase 11: TSA 23 BA-only WS4 consumer test

Parent issue: #52
Branch: `feature/p124-ba-consumer-test`
Status: active

Goal: map the published BA-only pilot to the compiled TSA 23 WS4 fragment grid,
add report-only fields to a copy, and run one validate/simulate consumer test
without changing the production dataset or model.

- [x] P124.1 Run the TSA 23 BA-only WS4 consumer test (#53)
  - [x] Verify the BA table and raster identity.
  - [x] Build the cell-to-fragment join and report match counts.
  - [x] Add the report-only fields to a copied dataset.
  - [x] Run `ws4 validate` and one bounded `ws4 simulate`.
  - [x] Write the report and JSON summary.
  - [x] Add the helper test, update the roadmap/changelog, and queue the PR.

Acceptance criteria:

- Valid cells match the raster; `-9999` is not treated as zero.
- Matched and unmatched cells are reported.
- The copied fragment and block tables carry the report-only fields.
- `ws4 validate` passes and the bounded simulation completes.
- The report states read/ignored/refused behavior.
- The production dataset and model are unchanged.
