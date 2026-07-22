# -*- coding: utf-8 -*-
r"""
prep_background_group.py

목적
- prep_target_group.py의 공통 전처리 함수를 사용하여 배경 승객군(Background group) 결과를 저장한다.
- 이후 배경 승객군의 평균/P95 대기시간 변화, 성공률 분석 등에 바로 쓸 수 있도록 데이터를 분리한다.

출력
- background_group_seed_metrics.csv
- background_group_waittime_long.csv
- background_group_condition_summary.csv
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


def build_background_group_tables(passenger_tidy: pd.DataFrame, seed_metrics: pd.DataFrame):
    # 1) seed-level background metrics
    bg_seed = seed_metrics[seed_metrics["Group"] == "Background"].copy()
    bg_seed = bg_seed.sort_values(["Scenario", "Condition", "Seed"]).reset_index(drop=True)

    # success rate 추가
    bg_seed["SuccessRate"] = np.where(
        bg_seed["N_rows"] > 0,
        bg_seed["N_success"] / bg_seed["N_rows"],
        np.nan,
    )

    # 2) passenger-level long table (배경 승객 관측치만 필터링)
    bg_long = passenger_tidy[passenger_tidy["PassengerGroup"] == "Background"].copy()
    bg_long = bg_long.sort_values(["Scenario", "Condition", "Seed", "PassengerID"]).reset_index(drop=True)

    # 배경 승객용으로 바로 쓰기 쉬운 컬럼만 남김
    keep_cols = [
        "Scenario", "Condition", "Seed", "PassengerID",
        "CallTime", "WaitTime", "ExpectedWaitTime", "IncreasedTime",
        "Success", "PassengerGroup"
    ]
    keep_cols = [c for c in keep_cols if c in bg_long.columns]
    bg_long = bg_long[keep_cols].copy()

    # 3) scenario-condition 요약표
    summary_rows = []
    for scenario in SCENARIO_PLOT_ORDER:
        for condition in CONDITION_ORDER:
            sub = bg_seed[
                (bg_seed["Scenario"] == scenario) &
                (bg_seed["Condition"] == condition)
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

    bg_summary = pd.DataFrame(summary_rows)
    return bg_seed, bg_long, bg_summary


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
DEFAULT_EXPERIMENT_DIR = PROJECT_ROOT / "data" / "raw"
DEFAULT_PREPROCESSED_DIR = PROJECT_ROOT / "data" / "processed" / "target"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "data" / "processed" / "background"


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
        help="배경 승객군 전용 전처리 결과 저장 폴더"
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

    bg_seed, bg_long, bg_summary = build_background_group_tables(passenger_tidy, seed_metrics)

    bg_seed.to_csv(
        os.path.join(args.output_dir, "background_group_seed_metrics.csv"),
        index=False,
        encoding="utf-8-sig"
    )
    bg_long.to_csv(
        os.path.join(args.output_dir, "background_group_waittime_long.csv"),
        index=False,
        encoding="utf-8-sig"
    )
    bg_summary.to_csv(
        os.path.join(args.output_dir, "background_group_condition_summary.csv"),
        index=False,
        encoding="utf-8-sig"
    )

    print("[완료] background_group_seed_metrics.csv")
    print("[완료] background_group_waittime_long.csv")
    print("[완료] background_group_condition_summary.csv")
    print()
    print(bg_seed[["Scenario", "Condition", "Seed", "N_rows", "MeanWait", "P95Wait", "SuccessRate"]].head(12).to_string(index=False))


if __name__ == "__main__":
    main()