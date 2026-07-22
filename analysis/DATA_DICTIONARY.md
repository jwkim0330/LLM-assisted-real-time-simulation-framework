# Data dictionary

## Raw passenger files

Files: `data/raw/<Scenario>/<Condition>/passengers_kpi_seed_<N>.csv`

| Column | Meaning |
|---|---|
| `scenario_info` | Internal run identifier |
| `passenger_id` | Passenger request identifier within a run |
| `psgrNum` | Number of passengers represented by the request |
| `dep_node` | Departure node identifier |
| `dep_node_expanded` | Original departure coordinates |
| `arr_node` | Arrival node identifier |
| `calltime` | Request time in simulation seconds |
| `shuttleid`, `shuttleID` | Assigned shuttle identifier |
| `expectedwaitingtime` | Expected waiting time at assignment |
| `expectedarrivaltime` | Expected arrival time at assignment |
| `waitstarttime` | Time waiting began |
| `boardingtime` | Boarding time |
| `success` | Whether service was completed successfully |
| `pathChanged` | Path-change indicator/count recorded by the simulator |
| `arrivaltime` | Actual arrival time |
| `increased_time` | Additional time associated with the assignment |

## Raw vehicle files

Files: `data/raw/<Scenario>/<Condition>/vehicle_kpi_seed_<N>.csv`

| Column | Meaning |
|---|---|
| `scenario_info` | Internal run identifier |
| `currenttime` | Simulation time of the vehicle-state record |
| `shuttle_id` | Shuttle identifier |
| `shuttle_state` | Recorded shuttle state |
| `cur_dst` | Current destination |
| `cur_node` | Current node |
| `cur_path` | Current route/path representation |
| `cur_psgr` | Current passenger identifiers |
| `cur_psgr_num` | Current onboard passenger count |

## Main processed files

- `data/processed/target/passenger_level_tidy.csv`: passenger-level tidy data with target/background labels
- `data/processed/target/seed_metrics_tidy.csv`: seed-level metrics by scenario, condition, and passenger group
- `data/processed/target/vehicle_seed_summary.csv`: seed-level vehicle summaries
- `data/processed/total/total_group_seed_metrics.csv`: total-passenger seed-level metrics
- `data/processed/background/background_group_seed_metrics.csv`: background-passenger seed-level metrics
- `data/processed/tables/`: manuscript-oriented statistical tables

The preprocessing code identifies the ten target requests using the scenario-specific injection time and coordinates recorded in `preprocessing/prep_target_group.py`.
