# TSA23 Instance Agent Operating Notes

## Scope

This file documents agent operating conventions for the `femic-tsa23-instance`
repository only. It supplements (not replaces) the parent FEMIC `AGENTS.md`.

## Bootstrap

Before running TSA23 commands in a new clone:

1. Create/activate local virtual environment and install deps:
   - PowerShell:
     ```powershell
     python -m venv .venv
     .venv\Scripts\Activate.ps1
     python -m pip install --upgrade pip setuptools wheel
     python -m pip install -r requirements.txt
     ```
2. Confirm toolchain:
   - `python -m femic --help`
   - `ruff --version`
   - `mypy --version`
   - `pytest --version`

## Instance Governance

- All tracked files must be public-safe: no credentials, personal paths, provider
  URLs, raw transcripts, or proprietary Patchworks bundle files.
- Use all-lowercase names for new FEMIC-controlled paths.
- Never publish machine-specific personal paths; normalize to repo-relative paths
  or environment variables.

## Rebuild Workflow

- Do not hand-edit generated artifacts.
- Follow the rebuild spec in `config/rebuild.yaml`.
- Run invariant checks after every rebuild.
- Sink evidence reports to `runtime/evidence/` (ignored).

## Roadmap Discipline

- Document plans in `ROADMAP.md` before implementation.
- Update `CHANGE_LOG.md` after each deliverable.
- Link governing GitHub issues in `ROADMAP.md`.
- Keep issue checklists current; close only after checklist completeness.

## GitHub Issue Hygiene

- Use `gh` for all GitHub operations when authenticated.
- Treat progress comments as mandatory for milestones.
- Use Type labels: Bug, Feature, Task — no duplicate work-kind labels.
- Close issues with final summary comment before closure.

## TSR and Data Boundaries

- Canonical discovery artifacts live under `metadata/tsr/` (tracked).
- Cached PDFs live in the user's local config directory (ignored).
- Reviewed/adopted instance-local facts live under `config/tsr/overlay.yaml`.
- Do not auto-promote unresolved candidate facts into live contracts.

## Out of Scope for P108

- No Patchworks model build, Matrix Builder run, or TIPSY/BTC execution.
- No raw TSR PDF text or extracted content in tracked files.
- No promotion of TSA23 facts into accepted model contracts.
