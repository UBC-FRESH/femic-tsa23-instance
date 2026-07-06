TSR Guidance
============

Timber Supply Review (TSR) documents are the primary source for TSA23 timber
supply policies, boundaries, and silviculture directives.

Discovery
---------

Use FEMIC TSR discovery surfaces:

.. code-block:: powershell

   femic tsr index
   femic tsr fetch --tsa 23
   femic tsr extract --tsa 23

Review Workflow
---------------

1. Extract candidate facts from fetched TSR documents.
2. Initialize the instance-local reviewed overlay:

.. code-block:: powershell

   femic tsr overlay-init --instance-root . --tsa 23

3. Inspect adopted-vs-canonical state:

.. code-block:: powershell

   femic tsr overlay-report

Important boundary
------------------

- Canonical discovery artifacts live under ``metadata/tsr/`` (tracked).
- Cached PDFs live in the user's local config directory (ignored).
- Reviewed/adopted instance-local facts live under ``config/tsr/overlay.yaml``.
- Do not auto-promote unresolved candidate facts into live instance contracts.
