Quick Start
===========

This guide takes a clean checkout to a running analysis on a Linux or macOS host. It
replaces the earlier submodule/PowerShell instructions, which described the original
development layout rather than this repository.

Prerequisites
-------------

- Python 3.10 or newer.
- About 3 GB of disk for the Python environment, and 200 MB for the data bundle.
- No Patchworks and no Windows. Patchworks is only needed to *rebuild* the export; the
  analyses run from the compiled data.

Install
-------

.. code-block:: bash

   git clone https://github.com/UBC-FRESH/femic-tsa23-instance.git
   cd femic-tsa23-instance
   python3 -m venv .venv
   . .venv/bin/activate
   python -m pip install --upgrade pip
   python -m pip install -r requirements.txt


**The data are not in the repository.** ``runtime/`` and ``output/`` are gitignored: they
are rebuilt artifacts, not source. A fresh clone can import the scripts but cannot run
an analysis until the data are in place.

Data
----

Two options, in order of preference.

*Use the runtime bundle.* It contains exactly the inputs the analyses read — the
fragment inventory, the block topology, the FBP stand curves, the fire-weather
scenarios, the bridge schedules, and the compiled WS4 datasets. It is a release asset,
not a tracked file, because it is 72 MB:

.. code-block:: bash

   curl -LO https://github.com/UBC-FRESH/femic-tsa23-instance/releases/download/data-2026-10-20/tsa23-runtime-bundle.tar.gz
   curl -LO https://github.com/UBC-FRESH/femic-tsa23-instance/releases/download/data-2026-10-20/tsa23-runtime-bundle.tar.gz.sha256
   sha256sum -c tsa23-runtime-bundle.tar.gz.sha256
   tar -xzf tsa23-runtime-bundle.tar.gz

Or, with the GitHub CLI, ``gh release download data-2026-10-20``.

*Rebuild from source.* Follow ``config/rebuild.yaml`` and the runbooks in ``runbooks/``.
This is the reproducible path, but it needs VDYP and BatchTIPSY (under Wine on Linux),
and Patchworks for the export, and it takes hours. It is the right path when the source
layers change, not when you want to run an experiment.

Verify the environment
----------------------

.. code-block:: bash

   python -c "import numpy, pandas, geopandas, scipy, cffdrs; print('ok')"

With the data in place, the harness check is fast and should print ``PASS``:

.. code-block:: bash

   python scripts/check_spread_equivalence.py \
     --cases runtime/fire/bridge_barrier_blocks.csv --ignitions 20

First analysis
--------------

One comparison, three patterns on a fixed footprint, about seven seconds:

.. code-block:: bash

   python scripts/bridge_matched_footprint.py \
     --blocks output/patchworks_ft/fragments/fragments.shp \
     --fuel-types runtime/fire/fbp_stand_curves.csv \
     --topology runtime/ws4/topology_tsa23.csv \
     --footprint-ha 20000 --treat-fraction 0.20 --treatment fb \
     --scenario p90 --ignitions 40 --duration-min 480 --wind-dir 225 \
     --seed 1 --footprint-seed 1 \
     --out runtime/fire/one_cell.json

Then a sweep over the knobs, and a read of where the cliff is:

.. code-block:: bash

   python scripts/sensitivity_screen.py --out runtime/fire/screen.csv

``runbooks/bridge-experiments.md`` explains every knob and what to expect from it.

WS4
---

WS4 is a separate repository with its own environment. The scripts that build or verify
WS4 datasets (``apply_fuel_treatment_economics.py``, ``add_fuel_break_treatment.py``,
``complete_hazard_feature.py``, ``add_surface_fuel_treatment.py``,
``verify_spread_account.py``) import ``ws4`` and must run with that environment:

.. code-block:: bash

   git clone https://github.com/UBC-FRESH/ws4.git
   cd ws4 && python3 -m venv .venv && . .venv/bin/activate && pip install -e .
   cd ../femic-tsa23-instance
   /path/to/ws4/.venv/bin/python scripts/verify_spread_account.py

Next steps
----------

- :doc:`overview` for the layout and the model chain.
- :doc:`rebuild-contract` for the reproducible rebuild.
- :doc:`troubleshooting` for known failures.
- :doc:`api/index` for the analysis functions.
