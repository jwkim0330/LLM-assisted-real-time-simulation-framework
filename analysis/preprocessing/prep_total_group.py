# -*- coding: utf-8 -*-
r"""
prep_total_group.py

목적
- prep_target_group.py의 공통 전처리 함수를 사용하여 전체 승객군(Total group) 결과를 저장한다.
- 이후 Figure 16(전체 승객군 mean/P95 paired plot), ECDF, success rate 분석 등에 바로 쓸 수 있게 만든다.

출력
- total_group_seed_metrics.csv
- total_group_waittime_long.csv
- total_group_condition_summary.csv
"""

import os
import argparse
from pathlib import Path
import numpy as np
import pandas as pd

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


def build_total_group_tables(passenger_tidy: pd.DataFrame, seed_metrics: pd.DataFrame):
    # 1) seed-level total metrics
    total_seed = seed_metrics[seed_metrics["Group"] == "Total"].copy()
    total_seed = total_seed.sort_values(["Scenario", "Condition", "Seed"]).reset_index(drop=True)

    # success rate 추가
    total_seed["SuccessRate"] = np.where(
        total_seed["N_rows"] > 0,
        total_seed["N_success"] / total_seed["N_rows"],
        np.nan,
    )

    # 2) passenger-level long table (전체 승객 관측치)
    total_long = passenger_tidy.copy()
    total_long = total_long.sort_values(["Scenario", "Condition", "Seed", "PassengerID"]).reset_index(drop=True)

    # 전체 승객용으로 바로 쓰기 쉬운 컬럼만 남김
    keep_cols = [
        "Scenario", "Condition", "Seed", "PassengerID",
        "CallTime", "WaitTime", "ExpectedWaitTime", "IncreasedTime",
        "Success", "PassengerGroup"
    ]
    keep_cols = [c for c in keep_cols if c in total_long.columns]
    total_long = total_long[keep_cols].copy()

    # 3) scenario-condition 요약표
    summary_rows = []
    for scenario in SCENARIO_PLOT_ORDER:
        for condition in CONDITION_ORDER:
            sub = total_seed[
                (total_seed["Scenario"] == scenario) &
                (total_seed["Condition"] == condition)
            ].copy()

            if sub.empty:
                continue

            summary_rows.append({
                "Scenario": scenario,
                "Condition": condition,
                "N_seeds": int(len(sub)),
                "Mean_of_MeanWait": float(sub["MeanWait"].mean()),
                "Median_of_MeanWait": float(sub["MeanWait"].median()),
                "Mean_of_P95Wait": float(sub["P95Wait"].mean()),
                "Median_of_P95Wait": float(sub["P95Wait"].median()),
                "Mean_of_SuccessRate": float(sub["SuccessRate"].mean()),
                "Median_of_SuccessRate": float(sub["SuccessRate"].median()),
            })

    total_summary = pd.DataFrame(summary_rows)
    return total_seed, total_long, total_summary


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
DEFAULT_EXPERIMENT_DIR = PROJECT_ROOT / "data" / "raw"
DEFAULT_PREPROCESSED_DIR = PROJECT_ROOT / "data" / "processed" / "target"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "data" / "processed" / "total"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--experiment_dir",
        type=str,
        default=str(DEFAULT_EXPERIMENT_DIR),
        help="원본 실험 데이터 폴더(data/raw) 경로"
    )
    parser.add_argument(
        "--preprocessed_dir",
        type=str,
        default=str(DEFAULT_PREPROCESSED_DIR),
        help="공통 전처리 CSV 저장/로드 폴더"
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default=str(DEFAULT_OUTPUT_DIR),
        help="전체 승객군 전용 전처리 결과 저장 폴더"
    )
    parser.add_argument(
        "--rebuild",
        action="store_true",
        help="기존 공통 전처리 CSV를 무시하고 다시 생성"
    )
    args = parser.parse_args()

    ensure_dir(args.preprocessed_dir)
    ensure_dir(args.output_dir)

    passenger_csv = os.path.join(args.preprocessed_dir, "passenger_level_tidy.csv")
    metrics_csv = os.path.join(args.preprocessed_dir, "seed_metrics_tidy.csv")
    vehicle_csv = os.path.join(args.preprocessed_dir, "vehicle_seed_summary.csv")

    # 공통 전처리 없으면 생성
    if args.rebuild or (not os.path.exists(passenger_csv)) or (not os.path.exists(metrics_csv)):
        passenger_tidy, seed_metrics, vehicle_summary = build_preprocessed_tables(args.experiment_dir)
        save_preprocessed_tables(passenger_tidy, seed_metrics, vehicle_summary, args.preprocessed_dir)
    else:
        passenger_tidy = pd.read_csv(passenger_csv)
        seed_metrics = pd.read_csv(metrics_csv)

    total_seed, total_long, total_summary = build_total_group_tables(passenger_tidy, seed_metrics)

    total_seed.to_csv(
        os.path.join(args.output_dir, "total_group_seed_metrics.csv"),
        index=False,
        encoding="utf-8-sig"
    )
    total_long.to_csv(
        os.path.join(args.output_dir, "total_group_waittime_long.csv"),
        index=False,
        encoding="utf-8-sig"
    )
    total_summary.to_csv(
        os.path.join(args.output_dir, "total_group_condition_summary.csv"),
        index=False,
        encoding="utf-8-sig"
    )

    print("[완료] total_group_seed_metrics.csv")
    print("[완료] total_group_waittime_long.csv")
    print("[완료] total_group_condition_summary.csv")
    print()
    print(total_seed.head(12).to_string(index=False))


if __name__ == "__main__":
    main()