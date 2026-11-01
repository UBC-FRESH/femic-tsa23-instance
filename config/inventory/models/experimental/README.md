# Experimental inventory model root

This is the default experimental model root for the TSA23 instance.

- `als_tsa23_idf_basal_area_regional_2026c.json` — linear BA card
- `als_tsa23_idf_gross_volume_regional_poly2_2026c.json` — `log_terms` volume card
- height — `../../als_tsa23_idf_lorey_height_2026.json`

Both experimental cards load through the standard FEMIC model reader.  The
volume card uses `model_type: log_terms` with constant, log, log-square, and
log-product terms.

## Standard CLI

```bash
femic lidar inventory \
  --bundle <validated-bundle> \
  --features <ba-features.csv> \
  --model-key ba \
  --instance-root <instance-root> \
  --output-dir <ba-output>

femic lidar inventory \
  --bundle <validated-bundle> \
  --features <volume-features.csv> \
  --model-key volume \
  --instance-root <instance-root> \
  --output-dir <volume-output>
```

`--model-key` resolves the card from `config/inventory/experimental.yaml`.  An
explicit `--model` path still works.

The full-grid feature export must contain `fragment_id` plus the card's raw
predictors.  The nonlinear volume card does not require a companion script.

## Status

Experimental only.  The four-plot high-biomass external check is not the full
validation set.  The independent BC IDF check covers 56 plots: BA RMSE 8.02
m2/ha (54 in range) and volume RMSE 62.93 m3/ha (44 in range).  The independent
TSA23 subset has 7 plots and BA RMSE 15.02; no independent TSA23 volume plot is
inside the predictor range.  The earlier leave-one-TSA23-tile-out check is BA
RMSE 6.188 and volume RMSE 25.473, but that set is small and partly used in model
selection.  Raw data and full-grid products stay in the data archive, not this
repository.
