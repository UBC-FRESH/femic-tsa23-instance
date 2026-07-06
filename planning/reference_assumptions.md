# TSA23 Bootstrap — Reference Assumptions

## How TFL6 was used (process/workflow maturity reference)

- **Copied:** Issue/roadmap discipline pattern, FreshForge workflow graph style,
  teaching docs trajectory, source-layer planning structure.
- **Adapted:** TSA code from `tfl6` → `tsa23`, rebuild spec placeholder values.
- **Rejected:** TFL6's specific source datasets, seral assumptions, TS28-specific
  TSR facts, any data that would be TSA23-specific.
- **Deferred:** FreshForge workflow graph files for actual rebuild automation
  (P109+).

## How TSA29 was used (structural/package reference)

- **Copied:** Package structure layout (`pyproject.toml`, `src/tsa23_femic/`,
  `tests/`), docs Sphinx scaffold (conf.py, index.rst with toctree), `.gitignore`
  patterns, rebuild.yaml format, CHANGE_LOG.md / ROADMAP.md conventions.
- **Adapted:** Package name from `tsa29_femic` → `tsa23_femic`, instance ID in
  rebuild spec, TSA code references throughout docs.
- **Rejected:** TSA29-specific source datasets, seral curves for TSA29, any
  TSA29 model design defaults, TSA29 TSR overlay facts.
- **Deferred:** Any TSA29-specific Patchworks runtime config files, MATS/VDYP
  fit results.

## Explicitly not borrowed from either reference

- No TSA23-specific numerical parameters (all deferred to P109+).
- No source layer paths that point to private or non-public data.
- No TSR text content extracted from PDFs.
- No Patchworks model XML, fragments, tracks, or accounts files.
- No credentials, provider URLs, personal paths, or local machine paths.
