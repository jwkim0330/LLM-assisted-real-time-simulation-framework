from __future__ import annotations

import argparse
import re
from pathlib import Path

import pandas as pd

SCENARIOS = ("Festival", "Lunch", "Holiday")
CONDITIONS = ("HILS_BURST", "MATH_UNIFORM", "MATH_POISSON")
EXPECTED_SEEDS = set(range(1, 101))
PASSENGER_REQUIRED_COLUMNS = {
    "scenario_info",
    "passenger_id",
    "calltime",
    "success",
    "dep_node_expanded",
    "waitstarttime",
    "boardingtime",
    "arrivaltime",
    "increased_time",
}
VEHICLE_REQUIRED_COLUMNS = {
    "scenario_info",
    "currenttime",
    "shuttle_id",
    "shuttle_state",
    "cur_node",
    "cur_psgr_num",
}


def seed_set(files: list[Path]) -> set[int]:
    values = set()
    for path in files:
        match = re.search(r"seed_(\d+)\.csv$", path.name)
        if match:
            values.add(int(match.group(1)))
    return values


def check_columns(path: Path, required: set[str]) -> None:
    columns = set(pd.read_csv(path, nrows=0).columns)
    missing = required - columns
    if missing:
        raise ValueError(f"{path} is missing columns: {sorted(missing)}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--raw-dir",
        type=Path,
        default=Path(__file__).resolve().parent / "data" / "raw",
    )
    args = parser.parse_args()
    raw_dir = args.raw_dir.expanduser().resolve()

    total_files = 0
    for scenario in SCENARIOS:
        for condition in CONDITIONS:
            directory = raw_dir / scenario / condition
            if not directory.is_dir():
                raise FileNotFoundError(f"Missing directory: {directory}")

            passenger_files = sorted(directory.glob("passengers_kpi_seed_*.csv"))
            vehicle_files = sorted(directory.glob("vehicle_kpi_seed_*.csv"))
            passenger_seeds = seed_set(passenger_files)
            vehicle_seeds = seed_set(vehicle_files)

            if passenger_seeds != EXPECTED_SEEDS:
                raise ValueError(
                    f"{directory}: passenger seeds differ from 1..100; "
                    f"missing={sorted(EXPECTED_SEEDS - passenger_seeds)}, "
                    f"extra={sorted(passenger_seeds - EXPECTED_SEEDS)}"
                )
            if vehicle_seeds != EXPECTED_SEEDS:
                raise ValueError(
                    f"{directory}: vehicle seeds differ from 1..100; "
                    f"missing={sorted(EXPECTED_SEEDS - vehicle_seeds)}, "
                    f"extra={sorted(vehicle_seeds - EXPECTED_SEEDS)}"
                )

            for path in passenger_files:
                check_columns(path, PASSENGER_REQUIRED_COLUMNS)
            for path in vehicle_files:
                check_columns(path, VEHICLE_REQUIRED_COLUMNS)
            total_files += len(passenger_files) + len(vehicle_files)
            print(
                f"OK: {scenario}/{condition} "
                f"({len(passenger_files)} passenger + {len(vehicle_files)} vehicle files)"
            )

    print(f"Validation passed: {total_files} CSV files across 9 conditions.")


if __name__ == "__main__":
    main()
