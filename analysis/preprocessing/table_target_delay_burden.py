# -*- coding: utf-8 -*-
r"""
analyze_delay_burden_share.py

목적
- passenger_level_tidy.csv를 이용해
  타겟 승객군이 전체 대기시간 부담에서 차지하는 비중을 계산한다.

출력
- Table_TargetDelayBurden_seed_level.csv
- Table_TargetDelayBurden_summary.csv
- Table_TargetDelayBurden_delta.csv
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

TARGET_GROUP_LABEL = "Target"


def paired_delta_and_p(df: pd.DataFrame, baseline: str, value_col: str):
    a = df[df["Condition"] == baseline][["Seed", value_col]].rename(columns={value_col: "A"})
    b = df[df["Condition"] == "Synchronized"][["Seed", value_col]].rename(columns={value_col: "B"})
    m = a.merge(b, on="Seed", how="inner").dropna()

    if len(m) == 0:
        return np.nan, np.nan, 0

    delta = m["B"] - m["A"]
    try:
        p = float(wilcoxon(m["B"], m["A"], alternative="two-sided").pvalue)
    except Exception:
        p = np.nan

    return float(np.median(delta)), p, int(len(m))


def build_seed_level_burden(passenger_tidy: pd.DataFrame) -> pd.DataFrame:
    df = passenger_tidy.copy()

    # 성공 승객만 대상으로 함
    df = df[df["Success"] == True].copy()
    df["WaitTime"] = pd.to_numeric(df["WaitTime"], errors="coerce")
    df = df.dropna(subset=["WaitTime"])

    rows = []

    for (scenario, condition, seed), g in df.groupby(["Scenario", "Condition", "Seed"], observed=False):
        total_wait_sum = g["WaitTime"].sum()
        total_success_n = len(g)

        target = g[g["PassengerGroup"] == TARGET_GROUP_LABEL].copy()
        target_wait_sum = target["WaitTime"].sum()
        target_success_n = len(target)

        target_wait_burden_share = target_wait_sum / total_wait_sum if total_wait_sum > 0 else np.nan
        target_success_share = target_success_n / total_success_n if total_success_n > 0 else np.nan
        excess_burden = target_wait_burden_share - target_success_share if pd.notna(target_wait_burden_share) and pd.notna(target_success_share) else np.nan

        rows.append({
            "Scenario": scenario,
            "Condition": condition,
            "Seed": seed,
            "TotalSuccessN": total_success_n,
            "TargetSuccessN": target_success_n,
            "TotalWaitSum": float(total_wait_sum),
            "TargetWaitSum": float(target_wait_sum),
            "TargetWaitBurdenShare": float(target_wait_burden_share),
            "TargetSuccessShare": float(target_success_share),
            "ExcessBurden": float(excess_burden),
        })

    out = pd.DataFrame(rows).sort_values(["Scenario", "Condition", "Seed"]).reset_index(drop=True)
    return out


def build_summary(seed_df: pd.DataFrame) -> pd.DataFrame:
    rows = []

    for scenario in SCENARIO_PLOT_ORDER:
        for condition in CONDITION_ORDER:
            sub = seed_df[
                (seed_df["Scenario"] == scenario) &
                (seed_df["Condition"] == condition)
            ].copy()

            if sub.empty:
                continue

            rows.append({
                "Scenario": scenario,
                "Condition": condition,
                "N_seeds": int(len(sub)),
                "Median_TargetWaitBurdenShare": float(sub["TargetWaitBurdenShare"].median()),
                "Median_TargetSuccessShare": float(sub["TargetSuccessShare"].median()),
                "Median_ExcessBurden": float(sub["ExcessBurden"].median()),
                "Mean_TargetWaitBurdenShare": float(sub["TargetWaitBurdenShare"].mean()),
                "Mean_TargetSuccessShare": float(sub["TargetSuccessShare"].mean()),
                "Mean_ExcessBurden": float(sub["ExcessBurden"].mean()),
            })

    return pd.DataFrame(rows)


def build_delta(seed_df: pd.DataFrame) -> pd.DataFrame:
    rows = []

    for scenario in SCENARIO_PLOT_ORDER:
        sub = seed_df[seed_df["Scenario"] == scenario].copy()

        for metric in ["TargetWaitBurdenShare", "ExcessBurden"]:
            for baseline in ["Uniform", "Poisson"]:
                delta_median, p_val, n_pairs = paired_delta_and_p(sub, baseline, metric)
                rows.append({
                    "Scenario": scenario,
                    "Metric": metric,
                    "Contrast": f"Synchronized - {baseline}",
                    "Median_Delta": delta_median,
                    "Wilcoxon_p": p_val,
                    "N_pairs": n_pairs,
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

    if args.rebuild or (not os.path.exists(passenger_csv)):
        passenger_tidy, seed_metrics, vehicle_summary = build_preprocessed_tables(args.experiment_dir)
        save_preprocessed_tables(passenger_tidy, seed_metrics, vehicle_summary, args.preprocessed_dir)
    else:
        passenger_tidy = pd.read_csv(passenger_csv)

    seed_df = build_seed_level_burden(passenger_tidy)
    summary_df = build_summary(seed_df)
    delta_df = build_delta(seed_df)

    seed_out = os.path.join(args.output_dir, "Table_TargetDelayBurden_seed_level.csv")
    summary_out = os.path.join(args.output_dir, "Table_TargetDelayBurden_summary.csv")
    delta_out = os.path.join(args.output_dir, "Table_TargetDelayBurden_delta.csv")

    seed_df.to_csv(seed_out, index=False, encoding="utf-8-sig")
    summary_df.to_csv(summary_out, index=False, encoding="utf-8-sig")
    delta_df.to_csv(delta_out, index=False, encoding="utf-8-sig")

    print("[완료] Seed-level :", seed_out)
    print("[완료] Summary    :", summary_out)
    print("[완료] Delta      :", delta_out)
    print()
    print(summary_df.to_string(index=False))
    print()
    print(delta_df.to_string(index=False))


if __name__ == "__main__":
    main()