# femic-tsa23-instance

TSA23 standalone FEMIC (Forest Estate Modelling Integration Core) instance for a
graduate-student MASc thesis modelling project.

## What this is

A self-contained, rebuildable TSA23 instance repository linked from the parent
FEMIC repo at `external/femic-tsa23-instance`. It follows:

- **TSA29 structural pattern**: installable `pyproject.toml`, `src/`, tests, config,
  runbooks, Sphinx docs, DataLad/public-data publication policy.
- **TFL6 process rigor**: issue/roadmap discipline, source-layer planning, THLB/model
  design phase sequencing, FreshForge workflow evolution, publication QA, teaching
  docs trajectory.

## Quick start

```powershell
# From the FEMIC parent repo root:
git submodule update --init --recursive external/femic-tsa23-instance
cd external/femic-tsa23-instance

# Bootstrap Python environment
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements.txt
```

See the [docs](./docs/) for TSA23-specific guidance, rebuild procedures, and the
student-facing modelling documentation.

## Rebuild contract

TSA23 rebuilds follow the FEMIC P13 canonical rebuild spec:

- `config/rebuild.yaml` defines required inputs, command steps, and invariants.
- Evidence reports sink to `runtime/evidence/`.
- Do not hand-edit generated artifacts; regenerate via the rebuild runner.

## Public safety

This repository tracks only public or thesis-approved data and configuration.
It does not contain:

- Credentials or provider endpoints
- Personal or machine-specific paths
- Raw TSR PDF text or transcripts
- Proprietary Patchworks bundle files (provide locally)

## License

Same license as parent FEMIC repository unless otherwise noted.

## Links

- Parent FEMIC repo: https://github.com/UBC-FRESH/femic
- TSA29 instance reference: https://github.com/UBC-FRESH/femic-tsa29-instance
- TFL6 instance reference: https://github.com/UBC-FRESH/femic-tfl6-instance
