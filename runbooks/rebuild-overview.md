# Rebuild Overview Runbook

## Purpose

Walk through the canonical rebuild process for the TSA23 instance using FEMIC P13
rebuild contract.

## Prerequisites

- Fresh clone of `UBC-FRESH/femic-tsa23-instance`
- Parent submodule initialized: `git submodule update --init --recursive`
- Virtual environment active with FEMIC installed
- Local Patchworks installation (proprietary)

## Steps

1. Run preflight validation:
   ```powershell
   femic prep validate-case --instance-root . --run-config config/run_profile.tsa23.yaml
   ```

2. Check rebuild spec:
   ```powershell
   # Review config/rebuild.yaml for required inputs and command steps
   cat config\rebuild.yaml
   ```

3. Execute dry-run (no mutation):
   ```powershell
   femic rebuild dry-run --instance-root .
   ```

4. Execute full rebuild:
   ```powershell
   femic rebuild run --instance-root .
   ```

## Expected Outputs

- `runtime/evidence/` populated with invariant check reports
- `tracks/features.csv`, `tracks/accounts.csv` generated (if Patchworks stage runs)
- All invariant checks pass or are documented as known warnings

## Failure Remediation

See individual runbooks for specific failure modes:
- Source layer issues → source-layer-materialization.md
- VDYP failures → vdyp-troubleshooting.md
- Patchworks issues → patchworks-preflight.md
