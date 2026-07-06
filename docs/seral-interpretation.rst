Seral Interpretation
====================

TSA23 seral trajectories define the sequence of stand development states over
time. This page provides guidance on interpreting TSA23 seral behavior within
the Patchworks/ForestModel framework.

Seral Trajectory Basics
-----------------------

Each stand in TSA23 belongs to a seral trajectory that determines:

- Which growth curves apply (natural/treated)
- What treatment states are available
- How area transitions between states over time

TSA23-specific notes about seral assumptions will be added once the Phase 4
model-design work is completed. For now, defer to TSA29 and TFL6 examples for
interpretation patterns.

Common Interpretations
----------------------

- ``managed``/``unmanaged`` refers to treatment eligibility, not stand origin
- ``natural``/``treated`` refers to curve provenance only
- Do not infer ``managed = treated`` or ``unmanaged = natural``
- Retention is orthogonal to origin: retention may move area from managed to
  unmanaged but does not change origin

For more detail, see the parent FEMIC docs on Patchworks model semantics.
