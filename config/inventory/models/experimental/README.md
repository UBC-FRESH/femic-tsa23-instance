# Experimental inventory model root

This is the research-only experimental model root for the TSA23 instance.
The default model config is `config/inventory/default.yaml`.

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
  --model-config config/inventory/experimental.yaml \
  --instance-root <instance-root> \
  --output-dir <volume-output>
```

`--model-key` resolves the card from `config/inventory/default.yaml`, which
contains height and BA only.  To use these research cards, including volume,
pass `--model-config config/inventory/experimental.yaml`.  An explicit
`--model` path still works.

The full-grid feature export must contain `fragment_id` plus the card's raw
predictors.  The nonlinear volume card does not require a companion script.

## Status

Experimental only.  The four-plot high-biomass external check is not the full
validation set.  The strict independent BC IDF check covers 38 plots: BA RMSE
8.86 m2/ha (36 in range) and volume RMSE 67.02 m3/ha (28 in range).  The
56-plot expanded check includes 18 fallback tiles at 6-11 years and gives 8.02
and 62.93.  The independent TSA23 subset has 7 plots and BA RMSE 15.02; no
independent TSA23 volume plot is inside the predictor range.  Raw data and
full-grid products stay in the data archive, not this repository.
