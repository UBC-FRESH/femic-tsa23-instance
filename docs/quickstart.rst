Quick Start
===========

This guide walks through setting up the TSA23 instance for the first time.

Prerequisites
-------------

- Python 3.10+
- Parent FEMIC repository with submodule initialized
- Local Patchworks installation (proprietary, not tracked)

Setup
-----

From the parent FEMIC repo root:

.. code-block:: powershell

   git submodule update --init --recursive external/femic-tsa23-instance
   cd external/femic-tsa23-instance
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   python -m pip install --upgrade pip setuptools wheel
   python -m pip install -r requirements.txt

First rebuild
-------------

See the :doc:`rebuild-contract` page for full details on rebuilding the instance.

.. code-block:: powershell

   femic prep validate-case --instance-root . --run-config config/run_profile.tsa23.yaml
   femic tsr index

Next steps
----------

- See :doc:`tsr-guidance` for TSR discovery and interpretation
- See :doc:`troubleshooting` for common issues and fixes
