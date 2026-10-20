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

Preflight with the shipped derived data
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The source layers are not in the clone, but they are in the lab's public-data corpus.
Point FEMIC at the corpus's **``data``** directory — not the corpus root, which appends
``bc/`` and still fails:

.. code-block:: bash

   export FEMIC_EXTERNAL_DATA_ROOT=/path/to/femic-public-data/data

This instance is a *derived-data* instance: the VDYP caches from the original build are
present as ``data/vdyp_*-tsa23.*``. The preflight looks for the unscoped base names, so
create the aliases once (dry run by default):

.. code-block:: bash

   python scripts/link_vdyp_caches.py --instance-root . --apply

Then a resume preflight passes without a fresh VDYP pass:

.. code-block:: bash

   femic prep validate-case --instance-root . \
     --run-config config/run_profile.tsa23.resume.yaml

Observed 2026-10-20: ``Case preflight passed ... targets=[23]``, with a Wine warning.
A **fresh** (non-resume) rebuild still needs Wine on ``PATH`` for VDYP; that is the only
toolchain dependency the resume profile avoids.

Without ``FEMIC_EXTERNAL_DATA_ROOT``:

.. code-block:: text

   $ femic prep validate-case --instance-root . \
       --run-config config/run_profile.tsa23.yaml
   Error: Missing Site productivity source: .../data/bc/siteprod/Site_Prod_BC.gdb
     (set FEMIC_EXTERNAL_DATA_ROOT or restore expected dataset path)

That is the current state of this checkout, and it is why issues `#3` and `#4` are open.

Declared graphs
~~~~~~~~~~~~~~~

The rebuild is declared, not improvised. Two FreshForge graphs and one overlay carry it:

.. code-block:: text

   workflows/freshforge/tsa23_materialization_overlay.yaml
   workflows/freshforge/tsa23_materialization_workflow.yaml
   workflows/freshforge/tsa23_model_build_workflow.yaml

``femic.materialization`` nodes check the toolchain, install the environment, initialize
the submodule and its annex, enable ``arbutus-s3``, materialize the archived paths, audit
availability, and write a report. ``femic`` nodes then run validate-case through
``export_patchworks``. Both graphs validate and plan without touching the tree:

.. code-block:: bash

   freshforge validate workflows/freshforge/tsa23_model_build_workflow.yaml
   freshforge plan     workflows/freshforge/tsa23_model_build_workflow.yaml

The materialization overlay lists only what is **archived**. Publicly resolvable inputs
are not in it; their commands live in :doc:`data-sources`.

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
