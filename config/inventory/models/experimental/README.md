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
  --model config/inventory/models/experimental/als_tsa23_idf_basal_area_regional_2026c.json \
  --features <ba-features.csv> \
  --output-dir <ba-output>

femic lidar inventory \
  --bundle <validated-bundle> \
  --model config/inventory/models/experimental/als_tsa23_idf_gross_volume_regional_poly2_2026c.json \
  --features <volume-features.csv> \
  --output-dir <volume-output>
```

The full-grid feature export must contain `fragment_id` plus the card's raw
predictors.  The nonlinear volume card does not require a companion script.

## Status

Experimental only.  The external check is four clustered TSA23 plots; the
leave-one-TSA-out volume RMSE is 16–67 m3/ha depending on region.  Raw data and
full-grid products stay in the data archive, not this repository.
