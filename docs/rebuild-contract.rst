Rebuild Contract
================

Two different things are called "the build" here, and only one of them works from a
clone. This page states which.

Analysing the model
-------------------

The supported path, and the one a student should use: take the released data bundle and
run the scripts.

.. code-block:: bash

   gh release download data-2026-10-20.1 \
     --pattern 'tsa23-runtime-bundle-2026-10-20.1.tar.gz*'
   sha256sum -c tsa23-runtime-bundle-2026-10-20.1.tar.gz.sha256
   tar -xzf tsa23-runtime-bundle-2026-10-20.1.tar.gz

That restores the fragment inventory, the topology, the FBP curves, the weather ladder,
the bridge schedules and the compiled WS4 datasets. Everything under :doc:`api/index`
then runs. See :doc:`quickstart` and ``runbooks/data-bundle.md``.

Rebuilding from source
----------------------

**This cannot run from a clean clone.** The source layers are not in the repository:
they are large, externally hosted, and deliberately not committed. The rebuild spec is
``config/rebuild.spec.yaml`` (a machine-readable step list) and ``config/rebuild.yaml``
(the input and invariant description).

Required inputs, none of which ship here
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

===========================================  ==========================================
input                                        where it must come from
===========================================  ==========================================
``data/vri/`` (or ``data/bc/vri/``)          BC VRI, materialized from the lab's data mirror
``data/siteprod/``                           BC Site Productivity, same mirror
``data/tsa/`` (or ``data/bc/tsa/``)          TSA administrative boundary
``reference/Patchworks/``                    licensed Patchworks install (Windows)
``config/tsr/overlay.yaml``                  **is** in the repository — reviewed overlay
===========================================  ==========================================

FEMIC finds the first four through ``FEMIC_EXTERNAL_DATA_ROOT``. Without it:

.. code-block:: text

   $ femic prep validate-case --instance-root . \
       --run-config config/run_profile.tsa23.yaml
   Error: Missing Site productivity source: .../data/bc/siteprod/Site_Prod_BC.gdb
     (set FEMIC_EXTERNAL_DATA_ROOT or restore expected dataset path)

That is the current state of this checkout, and it is why issues `#3` and `#4` are open.

What a rebuild does, in order
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. **Source discovery** — materialize and validate the source layers.
2. **Data materialization** — VDYP run, curve tables, AU assignment.
3. **TIPSY handoff** — generate BatchTIPSY inputs and run them (under Wine on Linux).
4. **Model input generation** — ``forestmodel.xml``, fragments, tracks.
5. **Patchworks runtime** — Matrix Builder; produces ``accounts.csv`` and friends.
6. **Evidence collection** — invariant reports under ``runtime/evidence/``.

Steps 3 and 5 are the practical blockers: BatchTIPSY is a Windows application (it runs
under Wine with ``wine-mono`` and ``xvfb-run``; see ``runbooks/btc-wine-handoff.md``), and
Patchworks is proprietary and Windows-only.

What is committed
~~~~~~~~~~~~~~~~~

The repository tracks code, configuration and the reviewed TSR overlay. It does not track
``data/``, ``output/`` or ``runtime/``. What you will find in a working tree after a
successful build is *derived* state:

- ``data/*.feather`` — VRI checkpoints, VDYP layers and curves
- ``data/04_output-tsa23.csv`` — BatchTIPSY output
- ``output/patchworks/`` — ``forestmodel.xml`` and the fragment inventory
- ``runtime/ws4/compiled*`` — WS4 datasets compiled from the export

Those are evidence that a build happened; they are not a build recipe.

Consequence for reproducibility
-------------------------------

A result can be reproduced from the released bundle and the recorded commands
(``planning/bridge_experiment_log.md``). It cannot be reproduced from source without the
external data mirror and the two Windows-dependent steps. State which one a claim rests
on when you cite it.
