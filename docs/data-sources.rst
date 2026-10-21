Data sources
============

Every raw input this instance consumes, how to obtain it, and whether it is archived.

The rule
--------

| bucket | test | action |
| --- | --- | --- |
| **resolve** | public, still served, and the tool can fetch it | no archive; document the command |
| **archive** | hard to find, non-public, or expensive to regenerate | annex on the Arbutus special remote |
| **discuss** | expensive *and* very large | case by case, recorded here |

A raw input that is **not** archived must have a command here that a new environment can
run. If a layer has no such command, it is archived or it is not a declared input — it
cannot be neither.

Register
--------

Statuses below were produced by running the resolver on 2026-10-20; re-run them before
trusting this page.

.. list-table::
   :header-rows: 1
   :widths: 26 12 12 50

   * - entity
     - role
     - bucket
     - resolution
   * - VRI 2025 (`VEG_COMP_LYR_R1_POLY`)
     - vegetation inventory
     - resolve
     - exact catalogue hit; direct download `veg_comp_lyr_r1_poly_2025.gdb.zip`
   * - VRI 2024
     - vegetation inventory
     - resolve
     - same layer family; year-indexed package
   * - BEC (`BEC_BIOGEOCLIMATIC_POLY`)
     - biogeoclimatic
     - resolve
     - exact hit; WFS (`wfs_getfeature_bbox`)
   * - TSA boundary (`FADM_TSA`)
     - administrative boundary
     - resolve
     - exact hit; no direct-download candidate — resolve then fetch/order
   * - OGMA, parks, wildlife habitat
     - land-use constraints
     - resolve
     - catalogue aliases exist in `femic/bcdc_catalog.py`
   * - Site productivity (`Site_Prod_BC.gdb`)
     - site index
     - **archive** or manual
     - only a weak catalogue hit (`Site Productivity (Version 8.0) Data Locator`); no direct download. FEMIC reads it, never fetches it.
   * - TSR corpus (18 PDFs)
     - overlay review source
     - resolve
     - `femic tsr fetch --tsa 23`
   * - BatchTIPSY output (`data/04_output-tsa23.csv`)
     - managed yields
     - **archive**
     - Windows/Wine run with curated inputs; not a download

Resolve commands
----------------

VRI
~~~

Preferred, and the only path that also creates the workspace:

.. code-block:: bash

   femic instance init --instance-root . --download-bc-vri

Inspect before committing to a multi-gigabyte download:

.. code-block:: bash

   femic data bcdc-resolve VEG_COMP_LYR_R1_POLY \
     --no-download-direct --summary-csv /tmp/vri.csv

Observed 2026-10-20: ``status=exact_hit``, top match *VRI - 2025 - Forest Vegetation
Composite Rank 1 Layer (R1)*, one direct download candidate, WFS available.

BEC, OGMA, parks, wildlife habitat
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   femic data bcdc-resolve BEC_BIOGEOCLIMATIC_POLY --no-download-direct
   femic data bcdc-fetch BEC_BIOGEOCLIMATIC_POLY \
     --instance-root . --aoi "your-aoi.geojson" --download-root data/downloads

``bcdc-fetch`` returns AOI-scoped vector files for layers that expose a WFS service.

TSA boundary
~~~~~~~~~~~~

The layer is ``FADM_TSA``; searching for "TSA boundary" returns weak hits, so use the
object name:

.. code-block:: bash

   femic data bcdc-resolve FADM_TSA --no-download-direct

Observed 2026-10-20: ``status=exact_hit``, *FADM - Timber Supply Areas (TSA) and Blocks
(TSB)*, no direct-download candidate. If the WFS path is unavailable, ``femic data
bcdc-order`` submits a DWDS order and ``bcdc-order-followup`` materializes it when ready.

TSR corpus
~~~~~~~~~~

FEMIC indexes the public BC Timber Supply Review document surface for every management
unit, not just this one. The tracked registry (`metadata/tsr/` in FEMIC) covers
**42 TSAs, 677 documents, cycles 1994-2024**.

.. code-block:: bash

   femic tsr index                   # refresh the registry (repo-tracked JSON)
   femic tsr fetch --tsa 23          # 18/18 PDFs cached
   femic tsr extract --tsa 23        # candidate facts from the cached PDFs
   femic tsr overlay-report --instance-root .   # adopted_source_layers_count: 17

TSA23's 18 documents span four cycles, which is the complete set for this unit:

| cycle | documents |
| --- | ---: |
| 1995 | 6 |
| 2001 | 6 |
| 2006 | 3 |
| 2012 | 3 |

The PDFs are user-local (`~/.femic/tsr/corpus`), not committed; the registry and the
extracted facts are the tracked surfaces.

Extraction
^^^^^^^^^^

.. code-block:: bash

   femic tsr extract --tsa 23 --output-path runtime/tsr/tsa23_candidate_facts.json

Observed 2026-10-21: 18 documents, 0 failures, 766 candidate facts — 428
`thlb_reference`, 165 `tipsy_input_candidate`, 134 `au_definition_candidate`, 21
`source_layer_candidate`, 18 `document_metadata`.

**Read it as an index, not as data.** The extractor is regex-based and most families are
table-of-contents entries and stray numbers: "A3.1", "Site index", "timber harvesting land
base is increased". Of the 21 source-layer candidates, 4 are noise and **17 are real BC
layer names, every one from p.8 of `23tsdp12.pdf`** — which independently confirms the
overlay's 17 adopted layers and the provenance it records. That, plus the page numbers on
every fact, is what the output is good for: it points you at the page that supports a
claim, it does not make the claim. These documents are also the grey literature
behind the thesis's management assumptions — see
`planning/literature_slash_hazard.md`, Part 2.

Not resolvable — archive or manual
----------------------------------

**Site productivity.** The catalogue returns only a data locator, and FEMIC expects a
prepared ``Site_Prod_BC.gdb`` at a path given by ``FEMIC_EXTERNAL_DATA_ROOT``. Until a
resolver exists, this file is archived on the Arbutus remote and materialized by the
instance's materialization workflow.

Declared but not wired
----------------------

``config/tsr/overlay.yaml`` adopts 17 TSR source layers, but only five are referenced in
FEMIC's pipeline code: VRI, BEC, OGMA, parks, and wildlife habitat. The other twelve
(cut blocks, fire history, recreation, terrain, landscape plans, ungulate winter range)
are declared metadata and are not read by the build. They therefore need no resolution
instruction yet — and the overlay should not imply that they do.

Verification
------------

After resolving, the instance should pass its own preflight:

.. code-block:: bash

   femic prep validate-case --instance-root . --run-config config/run_profile.tsa23.yaml

That is the check that currently fails when Site productivity is absent, and it is the
one to run first in a new environment.
