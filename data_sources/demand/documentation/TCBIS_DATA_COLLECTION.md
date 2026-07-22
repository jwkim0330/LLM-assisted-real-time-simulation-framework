# TCBIS Data Collection Information

## Data source

- System: Transportation Card Big Data Integrated Information System (TCBIS; Korean: 교통카드빅데이터 통합정보시스템)
- Indicator category: Route and Stop Indicators (노선·정류장 지표)
- Indicator: Station-level Usage Volume (정류장별 이용량)
- Observation period: May 11-24, 2024
- Variables used: hourly boarding and alighting volumes
- Study area: the predefined experimental area in Ansan, Republic of Korea, including the surrounding university campus and nearby urban area

## Stop inclusion rule

All public-transit stops located within the geographic boundary of the study area were included. No top-N ranking or minimum passenger-volume threshold was applied. This produced 441 TCBIS-derived stop locations in the processed simulation input.

## Historical retrieval procedure

The records were collected through the TCBIS station-level usage-volume interface using the following procedure:

1. Select the Route and Stop Indicators category and the Station-level Usage Volume indicator.
2. Set the observation period to May 11-24, 2024.
3. Identify a public-transit stop within the predefined study-area boundary.
4. retrieve the stop's hourly boarding and alighting records for the observation period.
5. Repeat the query for the included stops.
6. Combine the records by stop, date, and hour for processing.

The TCBIS interface may change over time. The essential retrieval fields are the stop identifier, stop name, observation date, and hourly boarding and alighting volumes.

## Additional campus locations

Twenty major campus locations were added because they were not represented as public-transit stops. These records are labeled `campus_estimated_point` in `location_metadata.csv`. Their coordinates and relative demand scores were assigned heuristically based on the practical experience of campus-affiliated stakeholders.

These 20 locations are scenario-based estimates and are not TCBIS observations.

## Dataset composition

| Source type | Locations | Basis |
|---|---:|---|
| `TCBIS_stop` | 441 | Observed station-level boarding and alighting records |
| `campus_estimated_point` | 20 | Stakeholder-informed heuristic estimates |
| Total | 461 | Combined simulation candidate locations |

## Third-party data and redistribution

TCBIS is a third-party data source. This package includes the exact processed `Demand.xlsx` used by the simulator, location-level provenance metadata, the documented collection and processing procedure, and one illustrative TCBIS export.

The illustrative export does not represent the complete set of raw stop records. Researchers seeking the original source records should access TCBIS and follow the provider's applicable access and reuse terms.
