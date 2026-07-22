# Expected reproduction results

A successful analysis run should report:

- 3 scenarios;
- 3 demand conditions per scenario;
- 100 seeds per scenario-condition combination;
- 900 simulation runs;
- 1,800 archived raw simulator-output CSV files.

The generated target-delay-burden summary should contain the following median target waiting-time burden shares:

| Scenario | Uniform | Poisson | Synchronized |
|---|---:|---:|---:|
| Festival | 0.1813 | 0.1859 | 0.2651 |
| Lunch | 0.1792 | 0.1984 | 0.2719 |
| Holiday | 0.1949 | 0.2198 | 0.2853 |

The principal output directories are:

- processed datasets and tables: `analysis/data/processed/`;
- generated figures: `analysis/figures/output/`.

Minor raster-size or text-wrapping differences may occur when Arial is unavailable. Numerical tables and plotted values should remain unchanged.
