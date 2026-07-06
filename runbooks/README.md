# TSA23 Instance Operator Runbooks

This directory contains operator-run guides for TSA23-specific workflows.

## Available Runbooks

- **rebuild-overview.md** — Canonical rebuild contract walkthrough
- **source-layer-materialization.md** — Materialize and validate source layers
- **vdyp-troubleshooting.md** — VDYP diagnostic workflow
- **patchworks-preflight.md** — Patchworks runtime preflight checklist

## Runbook Structure

Each runbook follows a consistent format:

1. Purpose — what this runbook solves
2. Prerequisites — what must be true before starting
3. Steps — numbered, executable commands
4. Expected outputs — what good looks like
5. Failure remediation — how to diagnose and recover

## Conventions

- All commands use relative paths from the instance root
- Commands that mutate data are clearly marked with ⚠️ WARNING
- Commands that should run in a virtual environment start with `.venv\Scripts\Activate.ps1`
- Evidence sinks go to `runtime/evidence/`
