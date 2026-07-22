# Analysis and figure-reproduction environment

This directory converts the archived simulator outputs into tidy datasets, statistical tables, and manuscript Figures 12-16.

## Reference environment

- Python 3.11
- Windows 10/11 with Arial is recommended for matching submitted raster dimensions
- Linux and macOS are supported through font fallbacks

## Installation

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## One-command reproduction

```powershell
python run_all.py
```

This command performs the following operations in order:

1. validates all 1,800 raw CSV files and their required columns;
2. rebuilds target-, total-, and background-group processed datasets;
3. rebuilds the success-rate and target-delay-burden tables;
4. regenerates Figures 12-16 as TIFF and PNG files.

Useful alternatives:

```powershell
python run_all.py --validate-only
python run_all.py --skip-preprocessing
python run_all.py --skip-figures
```

## Raw-data layout

```text
data/raw/
├── Festival/
│   ├── HILS_BURST/
│   ├── MATH_UNIFORM/
│   └── MATH_POISSON/
├── Lunch/
│   ├── HILS_BURST/
│   ├── MATH_UNIFORM/
│   └── MATH_POISSON/
└── Holiday/
    ├── HILS_BURST/
    ├── MATH_UNIFORM/
    └── MATH_POISSON/
```

Every condition directory must contain seeds 1-100 for both passenger and vehicle outputs.

## Individual preprocessing commands

```powershell
python preprocessing/prep_target_group.py
python preprocessing/prep_total_group.py
python preprocessing/prep_background_group.py
python preprocessing/table_success_rate.py
python preprocessing/table_target_delay_burden.py
```

All outputs are written under `data/processed/`.

## Individual figure commands

```powershell
python figures/scripts/figure12.py
python figures/scripts/figure13.py
python figures/scripts/figure14.py
python figures/scripts/figure15.py
python figures/scripts/figure16.py
```

All outputs are written under `figures/output/`.

Figure 12 is generated directly from the documented target-injection schedules. Figures 13-16 use CSV files under `data/processed/`.

## Font and pixel dimensions

The scripts select Arial when available. When Arial is unavailable, Liberation Sans or DejaVu Sans is used. A fallback font can change the final width by approximately one pixel; this does not change the data, statistical calculations, axes, or plotted values.

## Data definitions

See `DATA_DICTIONARY.md` for the raw and processed columns used by the analysis.
