# femic-tsa23-instance

TSA23 standalone FEMIC (Forest Estate Modelling Integration Core) instance for a
graduate-student MASc thesis modelling project.

## What this is

A self-contained TSA23 instance repository, intended to sit at
`external/femic-tsa23-instance` in a parent FEMIC checkout. It follows:

- **TSA29 structural pattern**: installable `pyproject.toml`, `src/`, tests, config,
  runbooks, Sphinx docs, DataLad/public-data publication policy.
- **TFL6 process rigor**: issue/roadmap discipline, source-layer planning, THLB/model
  design phase sequencing, FreshForge workflow evolution, publication QA, teaching
  docs trajectory.

## Quick start

```bash
git clone https://github.com/UBC-FRESH/femic-tsa23-instance.git
cd femic-tsa23-instance
python3 -m venv .venv && . .venv/bin/activate
python -m pip install -r requirements.txt

# The data are not in git. Take the released bundle:
gh release download data-2026-10-21 \
  --pattern 'tsa23-runtime-bundle-2026-10-21.tar.gz*'
sha256sum -c tsa23-runtime-bundle-2026-10-21.tar.gz.sha256
tar -xzf tsa23-runtime-bundle-2026-10-21.tar.gz
```

The repository is a **DataLad dataset**: the archived inputs under `data/` are git-annex
pointers, so a plain clone leaves them unresolved. The bundle above needs no special
remote; see `runbooks/data-bundle.md`.

Full instructions, including verification and a first analysis, are in
[`docs/quickstart.rst`](./docs/quickstart.rst) and published at
https://ubc-fresh.github.io/femic-tsa23-instance/.

## Rebuild contract

A from-source rebuild follows the FEMIC P13 spec (`config/rebuild.spec.yaml`,
`config/rebuild.yaml`), and **cannot run from a clean clone**: it needs the public-data
corpus plus Wine (for BatchTIPSY/VDYP) and, for the reference parity lane, a licensed
Patchworks install. The declared graphs live in `workflows/freshforge/`.

What a clone *can* do without a rebuild is analyse the released data bundle. The
distinction is written out in [`docs/rebuild-contract.rst`](./docs/rebuild-contract.rst).
Evidence reports sink to `runtime/evidence/`; do not hand-edit generated artifacts.

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
