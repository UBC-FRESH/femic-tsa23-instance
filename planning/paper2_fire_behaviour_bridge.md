# Paper 2: fuel-treatment effects and the WS4 spatial-account bridge (design)

Status: draft
Phase: fuel-treatment layer / Paper 2 modelling
Date: 2026-10-19

## The problem, at two scales

Paper 2 must predict the long-term effects of fuel-mitigation treatments:

1. **Aspatial, per hectare (stand scale).** A treatment changes stand fuel
   structure, which changes fire behaviour metrics — rate of spread (ROS),
   head-fire intensity (HFI), flame length, and crown-fire potential — and those
   effects evolve as the stand regrows. These are the **treatment curves** of
   Chapter 1, per analysis unit, and they map onto WS4 per-track feature/product
   accounts.
2. **Spatial, landscape scale.** The *arrangement* of treated and untreated fuel
   changes landscape fire behaviour — burn probability, area burned, and the
   intensity distribution — through fuel contiguity, patch size, and connectivity.
   This is the part WS4's **patch accounts** can carry.

The crux is to **approximate the stochastic spatial fire-spread model** with
WS4-compatible patch accounts: size classes, topology search distances,
sub-account targets, and weights.

## Fire-behaviour model

Per Leah Nash's recommendation (`fire-model-recommendation.md`), use the
**Canadian FBP System via `cffdrs`** (R `cffdrs`, or the official Python port
`cffdrs_py`) — the same system BCWS uses operationally.

- Inputs: FBP fuel type (from VRI: species, conifer %, crown closure; optional
  lidar canopy height / CBH / cover), weather (ERA5-Land or BCWS → FWI indices
  via `fwi()`), topography (DEM slope/aspect/elevation).
- Outputs: ROS (m/min), HFI (kW/m), flame length, crown-fire potential (CSI,
  CFB, fire-type class).
- Landscape spread: FBP gives *point/edge* behaviour; a **stochastic spatial
  spread model** (a Burn-P3-style Monte Carlo, or a raster percolation/spread
  model driven by FBP ROS) gives landscape outcomes (burn probability, area
  burned).

`FlamMap`/`FARSITE`/`Prometheus`/`Burn-P3` are Windows desktop wrappers around
the same equations and are a poor fit for a scripted, reproducible Linux
workflow; the code library plus a custom spread model is preferred.

## The bridge: fire simulation → WS4 patch accounts

The idea is a **response surface** compiled into WS4's spatial vocabulary:

1. **Define landscape fuel-pattern scenarios** — different treated area, patch
   size distribution, and spatial arrangement (random vs clumped vs fuel-break
   layouts).
2. **Run the stochastic fire-spread simulation** on each scenario, under a set
   of fire-weather scenarios (median and 90th-percentile fire-weather days).
3. **Record fire outcomes** — burn probability, area burned, and the intensity
   distribution — and the **pattern metrics** that describe each scenario
   (patch size distribution, contiguity, connectivity, edge density).
4. **Fit a response surface** `fire_outcome ~ f(pattern_metrics)`.
5. **Compile into WS4**: choose patch accounts whose `size_classes` and
   `search_distance` reproduce the pattern metrics that drive the outcome, then
   set sub-account targets (`area`, `size`, `frequency`, `shape`, `attractor`)
   and weights so the optimizer is steered toward low-risk patterns.

WS4 mechanics this uses (from `docs/reference/spatial.rst`):

- A **patch account** = a criteria feature curve + threshold + `size_classes` +
  `search_distance`; sub-accounts `area`, `size`, `shape`, `frequency`,
  `attractor` per size class.
- A **block topology** = undirected adjacency edgelist
  `src_block,dst_block,distance_m`; `search_distance` joins blocks that do not
  literally touch (a stand-in for spotting / ember transport and fuel
  continuity).
- **Spatial constraints**: maximum opening size, green-up, core area — the
  operational analogues of "do not create large contiguous fuel blocks".
- **Edge contrast** accounts measure juxtaposition of fuel types across shared
  edges (a fuel-break / WUI-adjacency lever).

## Concrete steps

1. **Build the TSA23 block topology** (adjacency + shortest distance) from the
   block/fragment geometry. One-off GIS step; enables every spatial account.
2. **Derive the FBP fuel type** for TSA23 from the VRI (species, conifer %,
   crown closure), baseline plus VRI-derived variants.
3. **Stand-scale treatment curves**: run FBP on pre- and post-treatment fuel
   types at each age; produce ROS/HFI/flame-length/crown-fire deltas per AU over
   time → WS4 feature accounts.
4. **Landscape scenarios**: rasterize fuel patterns and run the stochastic
   spread model per weather scenario.
5. **Response surface**: fit fire outcome vs pattern metrics.
6. **Compile to WS4**: patch accounts + targets + weights.
7. **Optimize** in WS4 and compare against the fire-simulation outcomes.

## Open questions

- Which stochastic spread model (custom FBP-driven percolation vs an existing
  open implementation)?
- Weather/topography data availability for TSA23 and the fire-weather scenario
  set.
- Raster-to-block aggregation and the criteria feature definition.
- How to price the response surface as a differentiable-enough target for the
  metaheuristic search.
