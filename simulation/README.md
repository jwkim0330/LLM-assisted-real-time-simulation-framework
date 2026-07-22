# Simulation environment

This directory generates the raw passenger- and vehicle-level CSV files used by the analysis pipeline.

## Reference environment

- Python 3.11
- CPU execution only; no GPU is required
- Windows 10/11 is the primary reference platform

## Installation

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Inputs

The simulator loads the following files from `JSON/`:

- `map_graph_with_vectors.json`: road-network graph
- `passengerInfo.json`: passenger-generation configuration
- `shuttleInfo.json`: shuttle configuration
- `setup.json`: simulation settings
- `Demand.xlsx`: time- and location-dependent background-demand inputs

The archived experiment uses six shuttles, a 3,600-second horizon, and 100 random seeds. These values are recorded in `JSON/setup.json` and the command below.

## Full experiment

```powershell
python Main_MobilitySim.py --scenarios all --conditions all --start-seed 1 --end-seed 100 --max-time 3600
```

For a quick smoke test:

```powershell
python Main_MobilitySim.py --scenarios HOLIDAY --conditions HILS_BURST --start-seed 1 --end-seed 1 --max-time 3600
```

## Command-line options

- `--scenarios`: `all` or a comma-separated subset of `FESTIVAL,LUNCH,HOLIDAY`
- `--conditions`: `all` or a comma-separated subset of `HILS_BURST,MATH_UNIFORM,MATH_POISSON`
- `--start-seed`, `--end-seed`: inclusive random-seed range
- `--max-time`: simulation horizon in seconds
- `--output-dir`: output root; default is `results_experiment/`

The simulator seeds NumPy and Python's `random` module from `CURRENT_SEED` for each run. Target-demand timing is controlled by the selected condition. The target scenario and condition are passed through environment variables by `Main_MobilitySim.py`; users do not need to edit source code.

## Outputs

```text
results_experiment/
├── Festival/
│   ├── HILS_BURST/
│   ├── MATH_UNIFORM/
│   └── MATH_POISSON/
├── Lunch/
└── Holiday/
```

Each condition contains:

- `passengers_kpi_seed_<N>.csv`
- `vehicle_kpi_seed_<N>.csv`

Transfer completed results into the analysis environment with:

```powershell
python copy_results_to_analysis.py --analysis-dir ..\analysis --overwrite
```

## Important implementation note

The original research snapshot hard-coded `HOLIDAY` in `Generator.py`. This public release exposes the scenario as `TARGET_SCENARIO` and makes `Main_MobilitySim.py` iterate all three scenarios, while preserving the experimental coordinates, target-demand rules, and KPI calculations.
