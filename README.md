# LLM-assisted real-time simulation framework

<a href="https://doi.org/10.5281/zenodo.19656741"><img src="https://zenodo.org/badge/1215498819.svg" alt="DOI"></a>

This repository holds two things: the DRT application ecosystem used to run the
framework, and the reproducibility package for the associated PLOS ONE study.

```text
.
├── drt_app/                    Flutter passenger application
├── drt_chatbot/                LLM chatbot interface
├── drt_simulator/              development DRT simulator
├── drt_system_manager/         operator-side system manager
├── drt_visualization/          visualization tools
│
├── simulation/                 DRT simulation code and executable input files (paper)
├── analysis/                   preprocessing, tables, and Figures 12-16
├── data_sources/demand/        demand provenance, metadata, and sample source file
├── validate_package.py         input and archived-output validation
└── EXPECTED_RESULTS.md         numerical checks for a successful reproduction
```

`simulation/` is the frozen, cleaned simulator used to produce the published
results. `drt_simulator/` is the working development tree and is not required to
reproduce the paper.

## Reproducibility package

This archive contains the processed simulation inputs, DRT simulator, archived outputs from 900 seeded runs, preprocessing and statistical-analysis code, and scripts used to produce Figures 12-16.

### What can be reproduced

The package separates three stages that should not be conflated:

1. Analysis and figures can be regenerated directly from the archived 1,800 simulator-output CSV files.
2. The 900-run experiment can be rerun from the supplied simulator and processed inputs.
3. The historical TCBIS demand-data acquisition and processing procedure are documented. The complete set of individual stop-query files and the original preprocessing script were not retained, but the exact processed `Demand.xlsx` used in the simulation is included.

The simulator and analysis pipeline intentionally use separate Python environments because their dependency sets differ.

### Recommended route: reproduce analyses and figures

This route does not rerun the simulator. It uses the archived results from all 900 runs under `analysis/data/raw/`.

Windows PowerShell:

```powershell
cd analysis
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python run_all.py
```

Linux or macOS:

```bash
cd analysis
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python run_all.py
```

The command validates 1,800 CSV files, rebuilds processed datasets and statistical tables, and writes Figures 12-16 to `analysis/figures/output/`.

### Validate the complete archive

After installing the analysis requirements, run from the repository root:

```bash
python validate_package.py
```

This validates the demand workbook, location metadata, required inputs, and the 1,800 archived simulation-output files.

### Optional route: rerun the simulator

Create a separate environment in `simulation/` and run:

```powershell
cd simulation
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python Main_MobilitySim.py --scenarios all --conditions all --start-seed 1 --end-seed 100 --max-time 3600
python copy_results_to_analysis.py --analysis-dir ..\analysis --overwrite
```

After the simulation finishes, use the analysis environment and run `python run_all.py` from `analysis/`.

For a one-run smoke test, see `simulation/README.md`.

### Demand input documentation

The simulator reads `simulation/JSON/Demand.xlsx`. Its provenance and processing are documented under `data_sources/demand/`:

- TCBIS source: Route and Stop Indicators, station-level usage volume;
- observation period: May 11-24, 2024;
- 441 TCBIS-derived stops;
- 20 stakeholder-informed campus-estimated locations;
- the 1,000-request stress-testing parameter and the resulting expected rate of 41.67 requests/hour;
- hour-specific spatial origin and destination weights;
- location-level provenance metadata; and
- one illustrative source export.

The detailed demand documentation is in `data_sources/demand/documentation/`. The file `MANUSCRIPT_DEMAND_METHODS_TEXT.md` provides manuscript wording consistent with the supplied code and processed input.

### Experimental directory mapping

```text
simulation/results_experiment/<Scenario>/<Condition>/
analysis/data/raw/<Scenario>/<Condition>/
```

Scenarios are `Festival`, `Lunch`, and `Holiday`. Internal condition names map to manuscript labels as follows:

| Internal folder | Manuscript label |
|---|---|
| `HILS_BURST` | Synchronized |
| `MATH_UNIFORM` | Uniform |
| `MATH_POISSON` | Poisson |

Each scenario-condition directory contains 100 passenger CSV files and 100 vehicle CSV files.

### Reference environment

Python 3.11 is the reference interpreter. Figure scripts prefer Arial on Windows and use Liberation Sans or DejaVu Sans as fallbacks. Font substitution may change raster dimensions slightly but does not change numerical results.

### Public archiving

Create a fixed release, archive it in a repository that assigns a persistent identifier, and place that identifier in the manuscript Data Availability Statement. Update the placeholders in `DATA_AND_CODE_AVAILABILITY_TEMPLATE.md` before release.

## License

The author-generated source code in this repository is released under the MIT License. See the `LICENSE` file for details.

Author-generated simulation outputs and analysis datasets are released under the Creative Commons Attribution 4.0 International License (CC BY 4.0), except where otherwise stated. See `LICENSE-DATA.md` for details.

TCBIS-derived data and other third-party materials remain subject to the access and reuse terms of their original providers and are not relicensed by this repository.
