# TSA 23 BA-only WS4 consumer test

Date: 2026-11-02
Status: consumer test complete; the BA pilot is readable and report-only.

## Purpose

Close the P122 consumer gap by mapping the published BA-only pilot to the compiled
TSA 23 WS4 fragment grid, adding report-only fields to a copy of the dataset, and
running one validate/simulate cycle. The production dataset and model are unchanged.

## Inputs

- Runtime bundle: `tsa23-runtime-bundle-2026-10-21.tar.gz`.
- Compiled dataset: `runtime/ws4/compiled_ft_econ`.
- BA table: `inventory_ba_pilot.parquet`.
- BA raster: `tsa23_ba_pilot_25m.tif` (EPSG:3157, 25 m, nodata `-9999`).
- Fragments: `output/patchworks_ft/fragments/fragments.shp` (EPSG:3005).
- Schedule: `runtime/fuel_ft_proto/ft_sched100.csv`, period 0 normalised to offset 0
  for a one-year test.

## Checks

| Check | Result |
| --- | ---: |
| BA table rows | 2,942,755 |
| Raster valid pixels | 2,942,755 |
| Table/raster maximum absolute difference | 1.9e-6 |
| Matched cells | 2,833,996 |
| Unmatched cells | 108,759 |
| Matched cell area | 177,124.75 ha |
| Matched fragments | 52,827 |
| Matched blocks | 41,719 |
| Full fragment area containing at least one BA cell | 308,541.8 ha |
| Matched BA mean / min / max | 23.95 / 10.73 / 42.01 m2/ha |

The 108,759 unmatched cells are 3.7% of the valid cells. They are outside the
fragment grid or on edges where the 25 m cell centre does not fall inside a
fragment polygon. They are not zero-BA cells.

Nodata `-9999` is excluded before the join; only the 2,942,755 valid cells enter.
The table and raster are identical at every valid cell.

## Consumer result

A copy of `compiled_ft_econ` received:

- fragment level: `inventory_ba_m2_ha`, `inventory_ba_available`, `inventory_ba_cells`;
- block level: `inventory_ba_m2_ha`, `inventory_ba_available`.

`ws4 validate` passed. A one-year `ws4 simulate` with the 100-block FT schedule
completed. `Simulator.from_dataset` loads the fragment fields, so the consumer
reads them. The simulator does not expose a block table; the block fields are
present in the dataset table but are not separately surfaced by the simulator.

The fields are report-only. They do not change the schedule, curves, THLB, AAC, or
any model behavior. The consumer reads the values; it ignores them for simulation
semantics.

## Reproduction

```bash
python scripts/verify_ba_pilot_consumer.py \
  --dataset runtime/ws4/compiled_ft_econ \
  --ba-table inventory_ba_pilot.parquet \
  --ba-raster tsa23_ba_pilot_25m.tif \
  --fragments output/patchworks_ft/fragments/fragments.shp \
  --schedule runtime/fuel_ft_proto/ft_sched100.csv \
  --output-dir runtime/ba_consumer_test \
  --years 1
```

## Limits

- The copy lives under `runtime/`; the production dataset is unchanged.
- The runtime bundle is a 2026-10-21 snapshot, not a fresh rebuild.
- The 25 m cell-to-fragment join is a rasterized fragment-id assignment, not a
  polygon overlay; edge cells can be unmatched.
- The test uses a 100-block FT schedule, not a production AAC run.
- The BA pilot remains 14.9% coverage and non-operational.

## Decision

The BA-only pilot is consumer-readable in WS4. It can be carried as a report-only
fragment/block attribute. It is not an operational inventory and does not enter the
model objective or AAC.
