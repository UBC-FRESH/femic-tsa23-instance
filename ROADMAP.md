# TSA23 Instance Roadmap

## Phase 0: Bootstrap (P108 — P108.2–P108.4)

- [x] Create `UBC-FRESH/femic-tsa23-instance` public repository (parent #302, child #298)
- [x] Add parent submodule under `external/femic-tsa23-instance` (child #298)
- [x] Bootstrap instance governance, structure, and package scaffold (child #299)
- [ ] Plan TSA23 source workflow and first build phases (child #300)
- [ ] Write delegated result report and open P108 PR (child #301)

## Phase 1: Source/Corpus Discovery and Materialization (P109 — tentative)

Define the initial TSA23 source-data workflow without executing heavy workflows.

- [ ] Audit available TSA23 TSR references and BC Data Catalogue layers
- [ ] Map materialization targets (VRI, SiteProd, boundaries, THLB/THNS)
- [ ] Define DataLad/public-data mirror strategy for required layers
- [ ] Create instance rebuild spec draft (`config/rebuild.yaml`)
- [ ] Materialize first-pass source layers locally

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
