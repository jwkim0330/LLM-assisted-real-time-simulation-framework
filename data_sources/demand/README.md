# Demand Input Documentation

This directory documents the provenance and use of the background-demand input for Experiment 3.

The exact executable input is:

`simulation/JSON/Demand.xlsx`

The workbook contains 461 candidate locations: 441 TCBIS-derived public-transit stops and 20 campus-estimated locations.

## Files

- `documentation/TCBIS_DATA_COLLECTION.md`: source system, observation period, stop inclusion rule, historical retrieval procedure, and treatment of campus locations.
- `documentation/DEMAND_DATA_PROCESSING.md`: spatial-weight construction, the 1,000-request parameter, the 41.67 requests/hour calculation, sampling behavior, target-demand injection, and reproducibility limitations.
- `documentation/MANUSCRIPT_DEMAND_METHODS_TEXT.md`: suggested manuscript wording consistent with the supplied code and data.
- `metadata/location_metadata.csv`: machine-readable location name, identifier, coordinates, source type, and evidence basis.
- `metadata/location_metadata.xlsx`: spreadsheet version of the same metadata.
- `sample_raw/`: one illustrative TCBIS export showing the source-file structure.

## Reproducibility scope

The simulator and downstream analyses can be reproduced from the supplied processed workbook. The complete historical TCBIS acquisition step cannot be rerun solely from this package because the complete set of raw stop-query files and the original preprocessing script were not retained.
