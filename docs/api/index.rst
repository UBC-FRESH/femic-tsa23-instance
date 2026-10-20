API reference
=============

The reference is generated from the docstrings and annotations in ``scripts/``. Every
public function is listed with its signature, its parameter types, and its return value.
Search this page before you call one of these functions. Add an entry here whenever you
add a module.

Fire behaviour and weather
--------------------------

The stand-scale FBP curves and the fire-weather scenarios feed every downstream
experiment. Run them in that order: weather first, curves second.

.. toctree::
   :maxdepth: 1

   fire_weather_scenarios
   fbp_stand_curves

Landscape spread and the bridge
-------------------------------

The network spread model and the experiments built on it. ``landscape_spread`` holds the
spread kernel; the others drive it at a footprint or on an explicit treated mask.

.. toctree::
   :maxdepth: 1

   landscape_spread
   bridge_matched_footprint
   export_bridge_footprint
   run_matched_footprint
   check_spread_equivalence
   sensitivity_screen
   verify_legacy_evidence
   ws4_bridge_test

Topology and treatments
-----------------------

.. toctree::
   :maxdepth: 1

   build_block_topology
   add_fuel_break_treatment
   add_surface_fuel_treatment
   complete_hazard_feature
   apply_fuel_treatment_economics
