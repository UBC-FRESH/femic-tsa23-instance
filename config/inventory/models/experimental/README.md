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

Experimental only.  The external check is four clustered TSA23 plots; the
leave-one-TSA23-tile-out check is BA RMSE 6.188 m2/ha and volume RMSE 25.473
m3/ha across 13 tiles and 18 plots.  The four-plot high-biomass tile remains
hardest (BA 6.670, volume 42.092).  The leave-one-TSA-out volume RMSE is 16–67
m3/ha depending on region.  Raw data and full-grid products stay in the data
archive, not this repository.
