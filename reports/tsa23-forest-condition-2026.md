# Forest condition report: tsa23-ba-pilot-2026

- **Scenario:** inv01-ba-pilot
- **Period:** 2026
- **Generated:** 2026-11-02T00:00:00Z
- **Review status:** draft
- **Status:** report-only; alerts are advisory, not operational decisions.

## Indicators

| Indicator | Value | Unit | Source | Status | Applicability |
| --- | ---: | --- | --- | --- | --- |
| basal_area | 23.87 | m2/ha | femic.inventory.als (2026.1) | ok | TSA23 IDF; BA-only pilot; 36 in-range strict independent plots |

## Alerts

| Code | Severity | Indicator | Advisory message |
| --- | --- | --- | --- |
| ba-coverage | watch | basal_area | BA-only pilot covers 14.9% of TSA 23; treat -9999 as abstention and do not use for operational decisions. |

## Provenance

- **instance:** femic-tsa23-instance@4170451
- **source:** metadata/inv01/tsa23_ba_pilot_manifest.json
- **model_card:** config/inventory/models/als_tsa23_idf_basal_area_2026.json
- **model_card_sha256:** c9d2c8de369af5cceb7070531d0e924452cab52b50de39d31dad3e831d82e5a9
- **acceptance:** notes/reports/inv01-tsa23-ba-pilot-acceptance.md

## Limits

- This card is report-only and does not change objectives, constraints, growth, or the solver.
- Alerts are advisory and must not be treated as operational decisions.
- Indicator applicability and review status must be checked before use.
