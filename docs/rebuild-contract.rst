Rebuild Contract
================

The TSA23 rebuild follows FEMIC P13 canonical rebuild contract. All steps,
required inputs, invariants, and evidence expectations are defined in:

- ``config/rebuild.yaml`` — the full rebuild spec with command steps and invariant checks.

Quick overview of rebuild steps (in execution order):

1. **Source discovery** — materialize and validate source layers
2. **Data materialization** — VDYP run, curve tables, AU assignment
3. **TIPSY handoff** — generate BatchTIPSY input files
4. **Model input generation** — forestmodel.xml, fragments, tracks/
5. **Patchworks runtime** — Matrix Builder, accounts validation
6. **Evidence collection** — invariant check reports to ``runtime/evidence/``

For detailed commands and failure remediation, consult the operator runbooks
in the ``runbooks/`` directory.
