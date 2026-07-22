# -*- coding: utf-8 -*-
r"""
make_success_rate_table.py

목적
- seed_metrics_tidy.csv를 이용해
  Scenario × Group 기준 성공률 비교표를 생성한다.

출력
- Table_SuccessRate_ByGroupAndScenario.csv

표 내용
- Uniform / Poisson / Synchronized 각 조건의 median success rate
- Synchronized - Uniform median delta
- Synchronized - Poisson median delta
- paired Wilcoxon p-value
"""

import os
import argparse
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import wilcoxon

try:
    # Package execution: python -m preprocessing.<script>
    from .prep_target_group import (
        build_preprocessed_tables,
        save_preprocessed_tables,
        ensure_dir,
        SCENARIO_PLOT_ORDER,
        CONDITION_ORDER,
    )
except ImportError:
    # Direct execution: python preprocessing/<script>.py
    from prep_target_group import (
        build_preprocessed_tables,
        save_preprocessed_tables,
        ensure_dir,
        SCENARIO_PLOT_ORDER,
        CONDITION_ORDER,
    )

GROUP_ORDER = ["Target", "Background", "Total"]


def median_iqr(x: pd.Series):
    vals = pd.to_numeric(x, errors="coerce").dropna().to_numpy(dtype=float)
    if len(vals) == 0:
        return (np.nan, np.nan, np.nan)
    return (
        float(np.median(vals)),
        float(np.percentile(vals, 25)),
        float(np.percentile(vals, 75)),
    )


def paired_delta_and_p(df: pd.DataFrame, baseline: str):
    a = df[df["Condition"] == baseline][["Seed", "SuccessRate"]].rename(columns={"SuccessRate": "A"})
    b = df[df["Condition"] == "Synchronized"][["Seed", "SuccessRate"]].rename(columns={"SuccessRate": "B"})
    m = a.merge(b, on="Seed", how="inner").dropna()

    if len(m) == 0:
        return np.nan, np.nan, 0

    delta = m["B"] - m["A"]
    try:
        p = float(wilcoxon(m["B"], m["A"], alternative="two-sided").pvalue)
    except Exception:
        p = np.nan

    return float(np.median(delta)), p, int(len(m))


def build_success_rate_table(seed_metrics: pd.DataFrame) -> pd.DataFrame:
    df = seed_metrics.copy()
    if "SuccessRate" not in df.columns:
        df["SuccessRate"] = np.where(df["N_rows"] > 0, df["N_success"] / df["N_rows"], np.nan)

    rows = []

    for scenario in SCENARIO_PLOT_ORDER:
        for group in GROUP_ORDER:
            sub = df[
                (df["Scenario"] == scenario) &
                (df["Group"] == group)
            ].copy()

            u_med, u_q1, u_q3 = median_iqr(sub[sub["Condition"] == "Uniform"]["SuccessRate"])
            p_med, p_q1, p_q3 = median_iqr(sub[sub["Condition"] == "Poisson"]["SuccessRate"])
            s_med, s_q1, s_q3 = median_iqr(sub[sub["Condition"] == "Synchronized"]["SuccessRate"])

            delta_s_u, p_s_u, n_s_u = paired_delta_and_p(sub, "Uniform")
            delta_s_p, p_s_p, n_s_p = paired_delta_and_p(sub, "Poisson")

            rows.append({
                "Scenario": scenario,
                "Group": group,

                "Uniform_Median": u_med,
                "Uniform_Q1": u_q1,
                "Uniform_Q3": u_q3,

                "Poisson_Median": p_med,
                "Poisson_Q1": p_q1,
                "Poisson_Q3": p_q3,

                "Synchronized_Median": s_med,
                "Synchronized_Q1": s_q1,
                "Synchronized_Q3": s_q3,

                "Delta_Sync_vs_Uniform_Median": delta_s_u,
                "Pvalue_Sync_vs_Uniform": p_s_u,
                "Npairs_Sync_vs_Uniform": n_s_u,

                "Delta_Sync_vs_Poisson_Median": delta_s_p,
                "Pvalue_Sync_vs_Poisson": p_s_p,
                "Npairs_Sync_vs_Poisson": n_s_p,
            })

    return pd.DataFrame(rows)


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
DEFAULT_EXPERIMENT_DIR = PROJECT_ROOT / "data" / "raw"
DEFAULT_PREPROCESSED_DIR = PROJECT_ROOT / "data" / "processed" / "target"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "data" / "processed" / "tables"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--experiment_dir",
        type=str,
        default=str(DEFAULT_EXPERIMENT_DIR),
    )
    parser.add_argument(
        "--preprocessed_dir",
        type=str,
        default=str(DEFAULT_PREPROCESSED_DIR),
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default=str(DEFAULT_OUTPUT_DIR),
    )
    parser.add_argument(
        "--rebuild",
        action="store_true",
    )
    args = parser.parse_args()

    ensure_dir(args.preprocessed_dir)
    ensure_dir(args.output_dir)

    passenger_csv = os.path.join(args.preprocessed_dir, "passenger_level_tidy.csv")
    metrics_csv = os.path.join(args.preprocessed_dir, "seed_metrics_tidy.csv")
    vehicle_csv = os.path.join(args.preprocessed_dir, "vehicle_seed_summary.csv")

    if args.rebuild or (not os.path.exists(passenger_csv)) or (not os.path.exists(metrics_csv)):
        passenger_tidy, seed_metrics, vehicle_summary = build_preprocessed_tables(args.experiment_dir)
        save_preprocessed_tables(passenger_tidy, seed_metrics, vehicle_summary, args.preprocessed_dir)
    else:
        seed_metrics = pd.read_csv(metrics_csv)

    table_df = build_success_rate_table(seed_metrics)
    out_csv = os.path.join(args.output_dir, "Table_SuccessRate_ByGroupAndScenario.csv")
    table_df.to_csv(out_csv, index=False, encoding="utf-8-sig")

    print("[완료] Success rate table:", out_csv)
    print()
    print(table_df.to_string(index=False))


if __name__ == "__main__":
    main()