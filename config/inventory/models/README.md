# TSA 23 IDF inventory pilot cards

These three cards are the FEMIC INV-01 TSA 23 IDF pilot models.  They are
explicit inputs to `femic lidar inventory`; FEMIC does not invent coefficients
at prediction time.

| Card | Attribute | Link | Output | Fit |
| --- | --- | --- | --- | --- |
| `als_tsa23_idf_lorey_height_2026.json` | Lorey height | identity | m | 14 FAIB PSP plots, 100 Mile House IDF |
| `als_tsa23_idf_basal_area_2026.json` | Basal area | log | m2/ha | same |
| `als_tsa23_idf_gross_volume_2026.json` | Gross volume | log | m3/ha | same |

The cards use first-return point-cloud metrics and exact FAIB plot support.
LOOCV RMSE is 0.688 m height, 4.414 m2/ha basal area, and 20.666 m3/ha volume.

## Applicability limits

The cards stop at `Lhmean` 14.1882 m for BA/volume and `Lhp95` 24.07 m for
height.  High-biomass IDF stands above those ranges are unsupported.  Three of
four external TSA 23 high-biomass plots were outside the BA/volume range, and
one was outside the height range.  The full-run map drops out-of-range cells
rather than extrapolating.  TSA 29 is an exploratory transfer experiment; TSA 22
(Okanagan) is not used for TSA 23 training.

## Status

These are **pilot cards, not an operational inventory**:

- 14 IDF plots, all used in leave-one-plot-out cross-validation.
- No independent P48/P49 validation.
- The full TSA 23 run mapped 64% of the TSA by tile footprint and 48% by cell
  area; 907 point-cloud tiles lacked a matching fine 1 m DEM.
- VRI screening and a four-plot external PSP check show the cards do not cover
  high-biomass IDF stands (`Lhmean` range ends at 14.1882 m).
- The TSA 29 high-biomass experiment is exploratory and is not published here
  as a card.

Evidence and caveats:

- `notes/reports/inv01-tsa23-idf-pilot.md`
- `notes/reports/inv01-tsa23-full-mosaic.md`
- `notes/reports/inv01-tsa23-vri-reconciliation.md`
- `notes/reports/inv01-tsa23-psp-holdout.md`

The raw data and 25 m products are archived in Chinook, not in git.  Do not use
these cards for operational TSA 23 decisions without independent field
validation and a broader high-biomass calibration.
