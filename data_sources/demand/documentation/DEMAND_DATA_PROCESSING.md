# Demand Input Construction and Use in Experiment 3

## 1. Scope

This document describes the processed background-demand input used in Experiment 3, the basis of the spatial demand weights, and the way the simulator generates request times and locations.

The authoritative simulation input is:

`simulation/JSON/Demand.xlsx`

The original preprocessing script used to create this workbook from the complete set of TCBIS records was not retained. Therefore, the reproducibility package provides the exact processed workbook used in the reported experiments, location-level provenance metadata, a sample TCBIS export, and the documented processing procedure.

## 2. Source data and candidate locations

Station-level public-transit usage data were obtained from the Transportation Card Big Data Integrated Information System (TCBIS), using the Route and Stop Indicators > Station-level Usage Volume indicator. The observation period was May 11-24, 2024.

All public-transit stops located within the geographic boundary of the study area were included. Stops were not selected using a top-N ranking or a minimum usage-volume threshold. The final input contains:

- 441 TCBIS-derived public-transit stops; and
- 20 additional campus locations.

The 20 campus locations were added because important activity locations inside the university campus were not represented as public-transit stops. Their coordinates and relative demand scores were assigned heuristically based on the practical experience of campus-affiliated stakeholders familiar with local movement patterns. These campus values are scenario-based estimates rather than directly observed TCBIS demand.

## 3. Construction of hourly spatial weights

The TCBIS source records contain hourly boarding and alighting volumes by stop and date. The records from the 14-day observation period were aggregated by stop and hour.

For each hour, boarding and alighting values were normalized separately across the combined set of 461 locations. Therefore:

- each hourly boarding column in `Demand.xlsx` sums to 1; and
- each hourly alighting column in `Demand.xlsx` sums to 1.

The boarding columns are used as relative origin-selection weights. The alighting columns are used as relative destination-selection weights. Thus, the TCBIS records determine the relative spatial distribution of background requests, not the overall number of simulated DRT requests.

## 4. Background-demand intensity

The total expected background demand was set to 1,000 requests over a 24-hour period. This value was selected to create a sufficiently active background operating environment for observing the effects of the ten concentrated target requests.

The generator calculates the temporal share of each hour by summing the boarding and alighting weights for that hour. Because each hourly boarding column sums to 1 and each hourly alighting column also sums to 1, the total weight for every hour is 2. The hourly share is therefore 1/24.

The expected request rate is calculated as:

`1,000 requests / 24 hours = 41.67 requests per hour`

The corresponding continuous-time rate is:

`41.67 / 3,600 = approximately 0.01157 requests per second`

Inter-arrival times are sampled from an exponential distribution using this rate. The realized number of background requests therefore varies across random seeds.

The generator is implemented using hourly piecewise-constant rates. With the supplied `Demand.xlsx`, all hourly rates are equal. The background-arrival process used in Experiment 3 is therefore a constant-rate Poisson process, which is a special case of the implemented NHPP framework.

## 5. Origin and destination sampling

For each generated background request:

1. the origin is sampled from the boarding-weight column for the current simulation hour; and
2. the destination is sampled independently from the alighting-weight column for the same hour.

The overall expected request rate is constant across hours, while the workbook contains hour-specific spatial origin and destination weights.

Experiment 3 uses a simulation horizon of 3,600 seconds beginning at simulation time 0. Consequently, the reported Experiment 3 runs use the first hourly spatial-weight interval in `Demand.xlsx`.

The current implementation does not explicitly resample when the same location is selected as both origin and destination.

## 6. Zero weights and spatial perturbation

When an hourly weight in `Demand.xlsx` is exactly zero, the simulator replaces it with 0.0001 before weighted sampling. The sampling function then normalizes the adjusted weights internally. A location with an original zero weight therefore retains a small nonzero selection probability.

The workbook stores WGS 84 latitude and longitude. Before simulation, coordinates are converted to internal units by subtracting 126 from longitude and 37 from latitude and multiplying by 10,000. Independent uniform jitter between -10 and 10 internal units is then added to each coordinate. This is equivalent to approximately plus or minus 0.001 degrees in each coordinate dimension.

## 7. Target-demand injection in Experiment 3

Ten target requests are added to the background demand at or after simulation time 1,500 seconds. Their origin-destination pair is fixed within each spatial scenario. Only the temporal distribution of the ten requests changes across conditions:

- Synchronized (`HILS_BURST`): all ten requests occur at 1,500 seconds;
- Uniform (`MATH_UNIFORM`): requests occur at 30-second intervals beginning at 1,500 seconds; and
- Poisson (`MATH_POISSON`): the first request occurs at 1,500 seconds and subsequent inter-arrival times are sampled from an exponential distribution with a mean of 30 seconds.

For a fixed scenario and random seed, the background-demand realization is held constant across the three target-demand conditions.

## 8. Reproducibility files

- `simulation/JSON/Demand.xlsx`: exact processed demand input used by the simulator.
- `data_sources/demand/metadata/location_metadata.csv`: machine-readable metadata for all 461 locations.
- `data_sources/demand/metadata/location_metadata.xlsx`: spreadsheet version of the metadata.
- `data_sources/demand/documentation/TCBIS_DATA_COLLECTION.md`: source, observation period, inclusion rule, and retrieval procedure.
- `data_sources/demand/sample_raw/`: illustrative TCBIS export showing the source-file format.
- `simulation/Models/ExperimentalFrame/Generator.py`: implementation of arrival-time generation, spatial sampling, coordinate perturbation, and target-demand injection.

## 9. Reproducibility boundary

The simulations and all downstream analyses can be reproduced using the supplied processed `Demand.xlsx`. The historical acquisition of all individual TCBIS stop records cannot be replayed solely from this archive because the complete set of raw stop-query files and the original preprocessing script were not retained.
