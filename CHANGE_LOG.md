# Change Log

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
