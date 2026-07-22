# -*- coding: utf-8 -*-
r"""
prep_target_group.py

목적
- data/raw 아래 원본 passenger / vehicle CSV를 직접 읽는다.
- 시나리오별 하드코딩된 타겟 조건(time, dep_x, dep_y)을 이용해 타겟 승객을 식별한다.
- passenger-level tidy table, seed-level metrics table, vehicle summary table을 생성한다.

출력
- passenger_level_tidy.csv
- seed_metrics_tidy.csv
- vehicle_seed_summary.csv
"""

import os
import re
import ast
import argparse
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd

# ---------------------------------------------------------
# 1. 사용자 실험 구조 기준 설정
# ---------------------------------------------------------
SCENARIOS = {
    "FESTIVAL": {
        "folder_name": "Festival",
        "plot_name": "Festival",
        "time": 1500.0,
        "dep_x": 126.83739657110384,
        "dep_y": 37.29762586758092,
        "arr_x": 126.85369272696458,
        "arr_y": 37.30999131775141,
    },
    "LUNCH": {
        "folder_name": "Lunch",
        "plot_name": "Lunch",
        "time": 1500.0,
        "dep_x": 126.8351539884716,
        "dep_y": 37.29677579144293,
        "arr_x": 126.83856396910281,
        "arr_y": 37.316062635101254,
    },
    "HOLIDAY": {
        "folder_name": "Holiday",
        "folder_aliases": ["Holiday", "Holliday"],
        "plot_name": "Holiday",
        "time": 1500.0,
        "dep_x": 126.8352535886907,
        "dep_y": 37.29247798602247,
        "arr_x": 126.85716970086038,
        "arr_y": 37.29072240793255,
    },
}

CONDITION_MAP = {
    "MATH_UNIFORM": "Uniform",
    "MATH_POISSON": "Poisson",
    "HILS_BURST": "Synchronized",
}

SCENARIO_PLOT_ORDER = ["Festival", "Lunch", "Holiday"]
CONDITION_ORDER = ["Uniform", "Poisson", "Synchronized"]

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
DEFAULT_EXPERIMENT_DIR = PROJECT_ROOT / "data" / "raw"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "data" / "processed" / "target"

# 좌표 비교는 소수점 6자리 반올림 기준
TARGET_GROUP_SIZE = 10
TARGET_TIME = 1500.0
COORD_ROUND = 6

# ---------------------------------------------------------
# 2. 유틸
# ---------------------------------------------------------
def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def parse_seed_from_filename(filename: str) -> int:
    m = re.search(r"seed_(\d+)\.csv$", filename)
    if not m:
        raise ValueError(f"seed 번호를 읽지 못했습니다: {filename}")
    return int(m.group(1))


def parse_xy(text) -> Tuple[float, float]:
    """
    "(126.83828823728997, 37.29620884844568)" -> (126.838288..., 37.296208...)
    """
    if pd.isna(text):
        return (np.nan, np.nan)

    s = str(text).strip()
    try:
        val = ast.literal_eval(s)
        return float(val[0]), float(val[1])
    except Exception:
        return (np.nan, np.nan)


def rounded_xy(x: float, y: float, ndigits: int = COORD_ROUND) -> Tuple[float, float]:
    return (round(float(x), ndigits), round(float(y), ndigits))


def gini_coefficient(values: np.ndarray) -> float:
    x = np.asarray(values, dtype=float)
    x = x[np.isfinite(x)]
    if len(x) == 0:
        return np.nan
    if np.min(x) < 0:
        x = x - np.min(x)
    mean_x = np.mean(x)
    if mean_x == 0:
        return 0.0
    diff_sum = np.abs(np.subtract.outer(x, x)).mean()
    return 0.5 * diff_sum / mean_x


# ---------------------------------------------------------
# 3. 원본 파일 수집
# ---------------------------------------------------------
def collect_raw_files(experiment_dir: str) -> pd.DataFrame:
    rows = []

    for scenario_key, cfg in SCENARIOS.items():
        folder_candidates = cfg.get("folder_aliases", [cfg["folder_name"]])
        scen_dir = None
        for folder_name in folder_candidates:
            candidate = os.path.join(experiment_dir, folder_name)
            if os.path.isdir(candidate):
                scen_dir = candidate
                break
        if scen_dir is None:
            expected = ", ".join(folder_candidates)
            raise FileNotFoundError(
                f"시나리오 폴더를 찾지 못했습니다: {experiment_dir} / [{expected}]"
            )

        for cond_folder, cond_name in CONDITION_MAP.items():
            cond_dir = os.path.join(scen_dir, cond_folder)
            if not os.path.isdir(cond_dir):
                raise FileNotFoundError(f"조건 폴더를 찾지 못했습니다: {cond_dir}")

            passenger_files = []
            vehicle_files = []

            for fname in os.listdir(cond_dir):
                full = os.path.join(cond_dir, fname)
                if fname.startswith("passengers_kpi_seed_") and fname.endswith(".csv"):
                    passenger_files.append((parse_seed_from_filename(fname), full))
                elif fname.startswith("vehicle_kpi_seed_") and fname.endswith(".csv"):
                    vehicle_files.append((parse_seed_from_filename(fname), full))

            passenger_map = dict(passenger_files)
            vehicle_map = dict(vehicle_files)

            common_seeds = sorted(set(passenger_map.keys()) & set(vehicle_map.keys()))
            for seed in common_seeds:
                rows.append({
                    "ScenarioKey": scenario_key,
                    "Scenario": cfg["plot_name"],
                    "Condition": cond_name,
                    "Seed": seed,
                    "PassengerCSV": passenger_map[seed],
                    "VehicleCSV": vehicle_map[seed],
                })

    df = pd.DataFrame(rows).sort_values(["Scenario", "Condition", "Seed"]).reset_index(drop=True)
    if df.empty:
        raise ValueError("수집된 원본 CSV가 없습니다.")
    return df


# ---------------------------------------------------------
# 4. 타겟 승객 식별
#    - 현재 sample passenger CSV 기준: calltime + dep_node_expanded 사용
#    - arr 좌표 컬럼이 있으면 나중에 추가 가능
# ---------------------------------------------------------
def mark_target_passengers(df: pd.DataFrame, scenario_key: str, condition_name: str) -> pd.DataFrame:
    """
    타겟 추출 규칙
    - Synchronized: calltime == 1500 and dep == scenario dep
    - Uniform/Poisson: calltime >= 1500 and dep == scenario dep 인 후보 중
      calltime 오름차순으로 최대 10명 추출

    주의
    - success와 무관하게 먼저 타겟 집단을 식별한다.
    - arr 좌표 컬럼이 실제 파일에 있으면 추가 필터링 가능하도록 hook를 열어둔다.
    """
    cfg = SCENARIOS[scenario_key]
    out = df.copy()

    if "calltime" not in out.columns:
        raise KeyError("passenger CSV에 calltime 컬럼이 없습니다.")
    if "dep_node_expanded" not in out.columns:
        raise KeyError("passenger CSV에 dep_node_expanded 컬럼이 없습니다.")

    out["calltime"] = pd.to_numeric(out["calltime"], errors="coerce")

    # 출발지 좌표 파싱
    dep_xy = out["dep_node_expanded"].apply(parse_xy)
    out["dep_x"] = dep_xy.apply(lambda x: x[0])
    out["dep_y"] = dep_xy.apply(lambda x: x[1])

    out["dep_x_r"], out["dep_y_r"] = zip(*out.apply(
        lambda r: rounded_xy(r["dep_x"], r["dep_y"], COORD_ROUND), axis=1
    ))
    target_dep_x_r, target_dep_y_r = rounded_xy(cfg["dep_x"], cfg["dep_y"], COORD_ROUND)

    dep_match = (
        (out["dep_x_r"] == target_dep_x_r) &
        (out["dep_y_r"] == target_dep_y_r)
    )

    # 도착지 좌표 컬럼이 있으면 같이 쓰도록 확장 가능
    arr_match = pd.Series(True, index=out.index)
    if "arr_node_expanded" in out.columns:
        arr_xy = out["arr_node_expanded"].apply(parse_xy)
        out["arr_x"] = arr_xy.apply(lambda x: x[0])
        out["arr_y"] = arr_xy.apply(lambda x: x[1])
        out["arr_x_r"], out["arr_y_r"] = zip(*out.apply(
            lambda r: rounded_xy(r["arr_x"], r["arr_y"], COORD_ROUND), axis=1
        ))
        target_arr_x_r, target_arr_y_r = rounded_xy(cfg["arr_x"], cfg["arr_y"], COORD_ROUND)
        arr_match = (
            (out["arr_x_r"] == target_arr_x_r) &
            (out["arr_y_r"] == target_arr_y_r)
        )

    if condition_name == "Synchronized":
        time_mask = np.isclose(out["calltime"], cfg["time"])
    else:
        time_mask = out["calltime"] >= cfg["time"]

    candidates = out[dep_match & arr_match & time_mask].copy()

    # 시간순 정렬 후 최대 10명
    sort_cols = ["calltime"]
    if "passenger_id" in candidates.columns:
        sort_cols.append("passenger_id")
    candidates = candidates.sort_values(sort_cols).copy()
    candidates["target_rank"] = np.arange(1, len(candidates) + 1)

    selected_idx = candidates.head(TARGET_GROUP_SIZE).index

    out["is_target"] = False
    out.loc[selected_idx, "is_target"] = True

    # 추출 진단용 메타데이터
    out["target_candidate_count"] = int(len(candidates))
    out["target_selected_count"] = int(min(len(candidates), TARGET_GROUP_SIZE))
    out["target_complete_10"] = int(min(len(candidates), TARGET_GROUP_SIZE) == TARGET_GROUP_SIZE)

    # 선택된 행에만 rank 부여
    out["target_rank"] = np.nan
    out.loc[selected_idx, "target_rank"] = np.arange(1, len(selected_idx) + 1)

    return out


# ---------------------------------------------------------
# 5. passenger 파일 1개 처리
# ---------------------------------------------------------
def process_passenger_file(csv_path: str, scenario_key: str, scenario_name: str,
                           condition_name: str, seed: int) -> Tuple[pd.DataFrame, pd.DataFrame]:
    df = pd.read_csv(csv_path)
    df = mark_target_passengers(df, scenario_key, condition_name)

    # 숫자형 정리
    for col in ["waitstarttime", "boardingtime", "expectedwaitingtime", "arrivaltime", "increased_time"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # success 정리
    if "success" in df.columns:
        df["success_bool"] = df["success"].astype(str).str.lower().isin(["true", "1", "yes"])
    else:
        df["success_bool"] = True

    # 실제 대기시간
    if "waitstarttime" in df.columns and "boardingtime" in df.columns:
        df["wait_time"] = df["boardingtime"] - df["waitstarttime"]
        df.loc[df["wait_time"] < 0, "wait_time"] = np.nan
        df.loc[~df["success_bool"], "wait_time"] = np.nan
    else:
        df["wait_time"] = np.nan

    # 타겟 관련 진단 정보
    target_df = df[df["is_target"]].copy()
    target_requested_n = int(len(target_df))
    target_success_n = int(target_df["success_bool"].sum())
    target_failed_n = int(target_requested_n - target_success_n)
    target_complete_10 = int(target_requested_n == TARGET_GROUP_SIZE)

    # passenger-level tidy
    tidy = pd.DataFrame({
        "Scenario": scenario_name,
        "Condition": condition_name,
        "Seed": seed,
        "PassengerID": df["passenger_id"] if "passenger_id" in df.columns else np.arange(len(df)) + 1,
        "CallTime": df["calltime"],
        "DepNode": df["dep_node"] if "dep_node" in df.columns else np.nan,
        "ArrNode": df["arr_node"] if "arr_node" in df.columns else np.nan,
        "DepNodeExpanded": df["dep_node_expanded"] if "dep_node_expanded" in df.columns else np.nan,
        "WaitStartTime": df["waitstarttime"] if "waitstarttime" in df.columns else np.nan,
        "BoardingTime": df["boardingtime"] if "boardingtime" in df.columns else np.nan,
        "WaitTime": df["wait_time"],
        "ExpectedWaitTime": df["expectedwaitingtime"] if "expectedwaitingtime" in df.columns else np.nan,
        "IncreasedTime": df["increased_time"] if "increased_time" in df.columns else np.nan,
        "Success": df["success_bool"],
        "PassengerGroup": np.where(df["is_target"], "Target", "Background"),
        "TargetRank": df["target_rank"],
        "TargetRequestedN_file": target_requested_n,
        "TargetSuccessN_file": target_success_n,
        "TargetFailedN_file": target_failed_n,
        "TargetComplete10_file": target_complete_10,
    })

    metric_rows = []
    for group_name, mask in {
        "Target": df["is_target"],
        "Background": ~df["is_target"],
        "Total": np.ones(len(df), dtype=bool),
    }.items():
        sub = df.loc[mask].copy()
        waits = sub["wait_time"].dropna().to_numpy(dtype=float)

        # Gini는 최소 2개 이상일 때만 계산
        if len(waits) >= 2:
            gini_val = float(gini_coefficient(waits))
        else:
            gini_val = np.nan

        metric_rows.append({
            "Scenario": scenario_name,
            "Condition": condition_name,
            "Seed": seed,
            "Group": group_name,
            "N_rows": int(len(sub)),
            "N_success": int(sub["success_bool"].sum()),
            "MeanWait": float(np.mean(waits)) if len(waits) > 0 else np.nan,
            "MedianWait": float(np.median(waits)) if len(waits) > 0 else np.nan,
            "P95Wait": float(np.percentile(waits, 95)) if len(waits) > 0 else np.nan,
            "Gini": gini_val,

            # 타겟 집단 진단용 메타
            "TargetRequestedN": target_requested_n,
            "TargetSuccessN": target_success_n,
            "TargetFailedN": target_failed_n,
            "TargetComplete10": target_complete_10,
        })

    metrics = pd.DataFrame(metric_rows)
    return tidy, metrics


# ---------------------------------------------------------
# 6. vehicle 파일 1개 처리
# ---------------------------------------------------------
def process_vehicle_file(csv_path: str, scenario_name: str, condition_name: str, seed: int) -> pd.DataFrame:
    df = pd.read_csv(csv_path)

    if "cur_psgr_num" in df.columns:
        df["cur_psgr_num"] = pd.to_numeric(df["cur_psgr_num"], errors="coerce")
    if "currenttime" in df.columns:
        df["currenttime"] = pd.to_numeric(df["currenttime"], errors="coerce")

    return pd.DataFrame([{
        "Scenario": scenario_name,
        "Condition": condition_name,
        "Seed": seed,
        "VehicleRecords": int(len(df)),
        "MaxOccupancy": float(df["cur_psgr_num"].max()) if "cur_psgr_num" in df.columns else np.nan,
        "MeanOccupancy": float(df["cur_psgr_num"].mean()) if "cur_psgr_num" in df.columns else np.nan,
        "LastTimestamp": float(df["currenttime"].max()) if "currenttime" in df.columns else np.nan,
    }])


# ---------------------------------------------------------
# 7. 전체 전처리
# ---------------------------------------------------------
def build_preprocessed_tables(experiment_dir: str):
    file_table = collect_raw_files(experiment_dir)

    passenger_tidy_all = []
    seed_metrics_all = []
    vehicle_summary_all = []

    for _, row in file_table.iterrows():
        ptidy, pmetrics = process_passenger_file(
            csv_path=row["PassengerCSV"],
            scenario_key=row["ScenarioKey"],
            scenario_name=row["Scenario"],
            condition_name=row["Condition"],
            seed=int(row["Seed"]),
        )
        vsummary = process_vehicle_file(
            csv_path=row["VehicleCSV"],
            scenario_name=row["Scenario"],
            condition_name=row["Condition"],
            seed=int(row["Seed"]),
        )

        passenger_tidy_all.append(ptidy)
        seed_metrics_all.append(pmetrics)
        vehicle_summary_all.append(vsummary)

    passenger_tidy = pd.concat(passenger_tidy_all, ignore_index=True)
    seed_metrics = pd.concat(seed_metrics_all, ignore_index=True)
    vehicle_summary = pd.concat(vehicle_summary_all, ignore_index=True)

    passenger_tidy["Scenario"] = pd.Categorical(passenger_tidy["Scenario"], categories=SCENARIO_PLOT_ORDER, ordered=True)
    passenger_tidy["Condition"] = pd.Categorical(passenger_tidy["Condition"], categories=CONDITION_ORDER, ordered=True)

    seed_metrics["Scenario"] = pd.Categorical(seed_metrics["Scenario"], categories=SCENARIO_PLOT_ORDER, ordered=True)
    seed_metrics["Condition"] = pd.Categorical(seed_metrics["Condition"], categories=CONDITION_ORDER, ordered=True)

    vehicle_summary["Scenario"] = pd.Categorical(vehicle_summary["Scenario"], categories=SCENARIO_PLOT_ORDER, ordered=True)
    vehicle_summary["Condition"] = pd.Categorical(vehicle_summary["Condition"], categories=CONDITION_ORDER, ordered=True)

    return passenger_tidy, seed_metrics, vehicle_summary


def save_preprocessed_tables(passenger_tidy: pd.DataFrame,
                             seed_metrics: pd.DataFrame,
                             vehicle_summary: pd.DataFrame,
                             output_dir: str) -> None:
    ensure_dir(output_dir)

    passenger_tidy.to_csv(
        os.path.join(output_dir, "passenger_level_tidy.csv"),
        index=False,
        encoding="utf-8-sig"
    )
    seed_metrics.to_csv(
        os.path.join(output_dir, "seed_metrics_tidy.csv"),
        index=False,
        encoding="utf-8-sig"
    )
    vehicle_summary.to_csv(
        os.path.join(output_dir, "vehicle_seed_summary.csv"),
        index=False,
        encoding="utf-8-sig"
    )


# ---------------------------------------------------------
# 8. main
# ---------------------------------------------------------
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--experiment_dir",
        type=str,
        default=str(DEFAULT_EXPERIMENT_DIR),
        help="원본 실험 데이터 폴더(data/raw) 경로"
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default=str(DEFAULT_OUTPUT_DIR),
        help="전처리 결과 저장 폴더"
    )
    args = parser.parse_args()

    passenger_tidy, seed_metrics, vehicle_summary = build_preprocessed_tables(args.experiment_dir)
    save_preprocessed_tables(passenger_tidy, seed_metrics, vehicle_summary, args.output_dir)

    # 간단 체크 출력
    print("[완료] passenger_level_tidy.csv")
    print("[완료] seed_metrics_tidy.csv")
    print("[완료] vehicle_seed_summary.csv")
    print()
    print(seed_metrics.head(12).to_string(index=False))


if __name__ == "__main__":
    main()