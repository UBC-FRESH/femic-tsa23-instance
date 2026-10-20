# Bridge experiments: running and varying the landscape fire comparison

Purpose: run the matched-footprint fire experiment, vary its knobs, and read the
results without rediscovering the harness. This is the entry point for exploring the
bridge; it is not a statement of findings.

## Prerequisites

- The instance virtualenv: `/home/gep/workspace/femic/.venv` (or your own with
  `requirements.txt` plus `scipy`).
- These artifacts, produced by the instance build:
  - `output/patchworks_ft/fragments/fragments.shp`
  - `runtime/fire/fbp_stand_curves.csv`
  - `runtime/ws4/topology_tsa23.csv`
- `scipy` is required for the fast solver. Without it, use `--method reference`, which is
  exact but ~38x slower.

## Steps

### 1. One comparison (three patterns, one footprint, one seed)

```bash
python scripts/bridge_matched_footprint.py \
  --blocks output/patchworks_ft/fragments/fragments.shp \
  --fuel-types runtime/fire/fbp_stand_curves.csv \
  --topology runtime/ws4/topology_tsa23.csv \
  --footprint-ha 20000 --treat-fraction 0.20 --treatment fb \
  --scenario p90 --ignitions 40 --duration-min 480 --wind-dir 225 \
  --seed 1 --footprint-seed 1 \
  --out runtime/fire/one_cell.json
```

About 7 seconds. `--footprint-seed` fixes the footprint; `--seed` varies the pattern
layout and the ignition draw. Hold the footprint fixed when comparing patterns, or you
are comparing different land.

### 2. A sweep over the knobs

```bash
python scripts/sensitivity_screen.py --out runtime/fire/sensitivity_screen.csv
```

Writes two CSVs: the raw per-pattern rows and a per-cell ranking table
(`*_orders.csv`). The summary printed at the end answers: does the barrier stay best,
and how large is the effect relative to the seed range.

### 3. A single masked run (WS4 masks)

```bash
python scripts/run_matched_footprint.py \
  --treated-blocks /path/to/treated_barrier.csv \
  --seed 1 --treat-ros-factor 0.3 --ignitions 50 --duration-min 480 --wind-dir 225 \
  --out runtime/fire/masked_barrier_seed1.json
```

About 5 seconds. This is the form used for the WS4-treated masks; the treated set comes
from a CSV, not from a pattern generator.

## Knobs

| knob | flag | current | what it does |
| --- | --- | --- | --- |
| treated fraction | `--treat-fraction` | 0.20 | share of the footprint treated; the main lever |
| footprint size | `--footprint-ha` | 20000 | area of the fixed cluster the patterns sit in |
| weather | `--scenario` | p90 | a fire-season quantile: `median`, `p60`-`p95`, `p90`, `extreme`. Regenerate the ladder with `scripts/fire_weather_scenarios.py --quantiles 0.5,0.6,...,0.98` then `scripts/fbp_stand_curves.py` |
| treated ROS multiplier | `--treat-ros-factor` | 0.05 for `fb` | how much slower fire moves in treated blocks; 1.0 is a control |
| ignitions | `--ignitions` | 40 | Monte Carlo sample; the mean is noisy at 40, the tail is not |
| duration | `--duration-min` | 480 | burn window |
| wind | `--wind-dir` | 225 | spread bearing; patterns are laid out relative to it |
| seed | `--seed` | 1 | pattern layout + ignition draw |
| footprint seed | `--footprint-seed` | 1 | which cluster; fix it for comparisons |
| solver | `--method` | fast | `reference` is the per-ignition loop, for checking |

## Expected outputs

- `mean_burned_ha`, `p90_burned_ha`: area burned per ignition, averaged over ignitions.
- `directed_largest_reach`, `directed_mean_reach`: connectivity of the untreated pattern.
- `cone60_largest_component_ha`, `cone60_percolation_ha`: WS4's fragmentation metric.
- `treated_ha`, `treated_blocks`: confirm the patterns are area-matched before comparing.

Read the seed range before the mean. At 40 ignitions the mean ranking has moved between
seeds; the p90 has been the more stable statistic.

## Known limits

- No suppression. No spot fires. One wind direction.
- Treated blocks slow spread; they do not stop it. The FB multiplier is 0.05, a 20x
  slowdown, which is close to a stop but not one.
- FBP fuel typing is rule-based from VRI species shares; it is not the provincial raster.
- Weather is ERA5 daily proxies at three points, not station observations.
- The spread is a network model on block adjacency, not a raster fire-growth model.

## Failure remediation

| symptom | cause | fix |
| --- | --- | --- |
| `ModuleNotFoundError: scipy` | venv without the docs/analysis extras | `pip install scipy`, or `--method reference` |
| all patterns identical | `--treat-ros-factor 1.0` | that is the control; use 0.05/0.3 |
| rankings jump between seeds | Monte Carlo noise at low ignitions | raise `--ignitions`, report the range |
| `directed_largest_reach` implausible | topology read as directed with one row per pair | use an explicit both-orientations topology; see `femic-tsa23-instance#13` |

## Related

- `planning/paper2_evidence_log.md` — the measured baselines and their corrections (E2e,
  E6, E7, E8).
- `femic-tsa23-instance#14` — the knob list and why nothing here is a locked claim.
- `scripts/check_spread_equivalence.py` — proves the fast solver matches the reference.
