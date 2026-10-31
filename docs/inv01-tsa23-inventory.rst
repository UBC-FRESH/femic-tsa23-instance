INV-01 TSA 23 Inventory Pilot
=============================

This is the public evidence surface for the FEMIC INV-01 TSA 23 inventory pilot.
It documents what was built, how it was checked, and why it is not an operational
inventory.

Model cards
-----------

The three cards live in ``config/inventory/models``:

- ``als_tsa23_idf_lorey_height_2026.json``
- ``als_tsa23_idf_basal_area_2026.json``
- ``als_tsa23_idf_gross_volume_2026.json``

They are fitted from 14 FAIB PSP plots in the 100 Mile House TSA IDF, using
LidarBC first-return point clouds and the exact FAIB plot support.  The reported
LOOCV RMSE is 0.688 m for Lorey height, 4.414 m2/ha for basal area, and
20.666 m3/ha for gross volume.

.. warning::

   These are 14-plot pilot cards.  They are not an operational TSA 23
   inventory and have no independent P48/P49 validation.

What was run
------------

The full-domain pilot used 5,899 point-cloud/DEM tile pairs in 93 Sockeye
batches, a 25 m grid in EPSG:3157 with origin ``(549275, 5784675)``, and the
three cards.  It produced 9,523,476 feature cells, 6,573,196 height-domain
cells, and 2,942,755 BA/volume-domain cells.

Coverage is **64% by tile footprint and 48% by modelled cell area**:

- 907 point-cloud tiles had no matching fine 1 m DEM;
- 24 tiles had no usable first returns;
- 2,466 km2 of TSA 23 has no selected public point cloud.

See ``notes/reports/inv01-tsa23-full-mosaic.md`` for timings, Globus task IDs,
hashes, and reproduction links, and ``notes/reports/inv01-tsa23-gap-priority.md``
for the omitted-tile map.

Independent checks
------------------

VRI screening
   The full surface disagrees with VRI far more than the LOOCV errors suggest:
   height bias -2.48 m / RMSE 7.65 m, BA +4.61 / 11.49, volume +29.46 / 92.83 at
   cell level.  VRI is an interpreted polygon inventory, not independent field
   truth.  See ``notes/reports/inv01-tsa23-vri-reconciliation.md``.

PSP holdout
   Four external TSA 23 IDF plots were processed from the complete FAIB PSP
   archive.  They are high-biomass stands and three of four are outside the
   published BA/volume range, so this is an extrapolation stress test rather
   than an in-domain validation.  Height RMSE 1.46 m, BA 8.35 m2/ha, volume
   118.21 m3/ha.  See ``notes/reports/inv01-tsa23-psp-holdout.md``.

High-biomass experiment
   An exploratory TSA 29 (Williams Lake) increment improved the four-plot
   holdout for BA and volume but not height, and the volume bias remained
   +53 m3/ha.  It is **not published** as model cards.  TSA 22 (Okanagan) is
   excluded from TSA 23 training and is transfer-test-only.  See
   ``experiments/inv01-high-biomass/``.  The archive audit and acquisition
   shortlist are in
   ``notes/reports/inv01-tsa23-high-biomass-acquisition-targets.md``.

Regional open-data calibration
   Using the full BC PSP + LidarBC set, 24 high-biomass IDF plots produced
   features; 19 non-TSA-23 plots supplement the 14 TSA 23 training plots.  The
   regional volume candidate reduces the four-plot external RMSE from 118.2 to
   42.5 m3/ha and bias from +89.3 to -3.4.  The BA candidate also improves
   (8.35 -> 6.67 m2/ha); height keeps the current card.  These are experimental,
   not published operational cards.  The default experimental model root is
``config/inventory/models/experimental/``.  It contains the linear BA card and
the term-based nonlinear volume card; both load through the standard FEMIC
reader.  ``config/inventory/experimental.yaml`` records the model set and
coverage.  The paired hybrid evidence remains under
``experiments/inv01-regional-calibration/hybrid_bundle/``.  Standard CLI parity
is documented in ``notes/reports/inv01-tsa23-cli-parity.md``.

Data and provenance
-------------------

Raw LidarBC data, DEMs, batch parts, and 25 m products are archived in Chinook.
The public repository contains the model cards, reports, tabular evidence,
figures, and the priority GeoPackage; it does **not** contain the raw point
clouds or the 2.16 TB archive.

The parent FEMIC repository carries the reusable extractor and runbook
``examples/inv01_tsa23_full``.  Project working data belongs on the data drive
under ``/srv/shared-data/gep/ws4/tmp/inv01-data``, never in ``/tmp``.

Model status
------------

The current surface has BA/volume on 14.9% of TSA 23 and height on 33.3%.  A
three-band 25 m status mask labels no-point-cloud, omitted/no-DEM,
processed/no-cell, height-only, and BA/volume-valid areas.  Applying the
experimental regional BA/volume candidates raises joint BA/volume coverage to
**23.6%** while height stays unchanged.  The masks and full-grid application
are documented in ``notes/reports/inv01-tsa23-model-status.md`` and
``notes/reports/inv01-tsa23-regional-inventory.md``.

.. figure:: /_static/inv01-tsa23-model-status.png
   :alt: TSA 23 model status mask
   :width: 100%

   Current pilot model-status mask.

Decision
--------

Use the current cards and the regional candidates as open-data pilot products,
not operational inventory.  The hybrid BA/volume bundle is the instance's
default experimental root; height keeps the current card.  Joint BA/volume
coverage rises to 23.6%.  A leave-one-TSA23-tile-out check across 13 tiles and
18 plots gives BA RMSE 6.188 m2/ha and volume RMSE 25.473 m3/ha; the four
clustered high-biomass plots remain the hardest fold, and cross-region transfer
is mixed.  See ``notes/reports/inv01-tsa23-hybrid-vs-current.md`` and
``notes/reports/inv01-tsa23-spatial-holdout.md``.

Evidence index
--------------

- ``notes/reports/inv01-tsa23-idf-pilot.md``
- ``notes/reports/inv01-tsa23-full-mosaic.md``
- ``notes/reports/inv01-tsa23-vri-reconciliation.md``
- ``notes/reports/inv01-tsa23-psp-holdout.md``
- ``notes/reports/inv01-tsa23-gap-priority.md``
- ``experiments/inv01-high-biomass/``
- ``notes/reports/inv01-tsa23-hybrid-vs-current.md``
- ``notes/reports/inv01-tsa23-spatial-holdout.md``
