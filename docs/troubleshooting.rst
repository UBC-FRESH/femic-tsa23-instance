Troubleshooting
===============

This page covers common issues encountered during TSA23 instance builds.

VDYP Fails
----------

Symptom: VDYP subprocess exits with non-zero code.

Common causes:
- Missing or corrupted VDYP input files
- Insufficient memory for large strata
- Wine/VDYP installation issues on Windows

Remediation:
1. Run ``femic prep validate-case`` to check required inputs
2. Check ``runtime/evidence/`` for VDYP-specific error reports
3. Try a debug run with ``--debug-rows 500`` to isolate problematic plots

Curve Table Issues
------------------

Symptom: Zero yields for species with nonzero source share, or unexpected curve counts.

Remediation:
1. Verify AU/curve mapping completeness
2. Check VDYP diagnostic logs in ``runtime/evidence/``
3. Run ``femic vdyp report`` to inspect fit diagnostics

Patchworks Matrix Builder Fails
--------------------------------

Symptom: Matrix Builder exits with errors related to tracks or accounts.

Common causes:
- Missing or malformed ``forestmodel.xml``
- Incomplete feature/product/source mappings in ``features.csv``
- ``accounts.csv`` doesn't match expected topology

Remediation:
1. Run ``femic prep validate-case`` before Matrix Builder execution
2. Inspect regenerated ``tracks/features.csv`` and ``tracks/accounts.csv`` for completeness
3. Verify species-share sanity: nonzero source share must produce nonzero runtime signal
