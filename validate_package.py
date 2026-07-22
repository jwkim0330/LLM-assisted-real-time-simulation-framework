from __future__ import annotations

import csv
import subprocess
import sys
from collections import Counter
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent


def fail(message: str) -> None:
    raise SystemExit(f"ERROR: {message}")


def validate_required_files() -> None:
    required = [
        ROOT / "simulation" / "JSON" / "Demand.xlsx",
        ROOT / "simulation" / "JSON" / "map_graph_with_vectors.json",
        ROOT / "simulation" / "JSON" / "passengerInfo.json",
        ROOT / "simulation" / "JSON" / "setup.json",
        ROOT / "simulation" / "JSON" / "shuttleInfo.json",
        ROOT / "data_sources" / "demand" / "metadata" / "location_metadata.csv",
        ROOT / "analysis" / "run_all.py",
    ]
    missing = [str(path.relative_to(ROOT)) for path in required if not path.exists()]
    if missing:
        fail("missing required files: " + ", ".join(missing))


def validate_demand_workbook() -> None:
    path = ROOT / "simulation" / "JSON" / "Demand.xlsx"
    df = pd.read_excel(path, header=1)
    df = df.loc[:, ~df.columns.astype(str).str.startswith("Unnamed:")]
    if len(df) != 461:
        fail(f"Demand.xlsx contains {len(df)} locations; expected 461")

    boarding = [column for column in df.columns if "(승차)" in str(column)]
    alighting = [column for column in df.columns if "(하차)" in str(column)]
    if len(boarding) != 24 or len(alighting) != 24:
        fail(
            f"Demand.xlsx contains {len(boarding)} boarding and {len(alighting)} "
            "alighting columns; expected 24 each"
        )

    tolerance = 1e-6
    bad_boarding = {
        column: float(df[column].sum())
        for column in boarding
        if abs(float(df[column].sum()) - 1.0) > tolerance
    }
    bad_alighting = {
        column: float(df[column].sum())
        for column in alighting
        if abs(float(df[column].sum()) - 1.0) > tolerance
    }
    if bad_boarding or bad_alighting:
        fail(
            "hourly Demand.xlsx columns do not sum to 1: "
            f"boarding={bad_boarding}, alighting={bad_alighting}"
        )

    print("OK: Demand.xlsx (461 locations; 24 boarding + 24 alighting columns)")


def validate_location_metadata() -> None:
    path = ROOT / "data_sources" / "demand" / "metadata" / "location_metadata.csv"
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != 461:
        fail(f"location_metadata.csv contains {len(rows)} rows; expected 461")
    counts = Counter(row["source_type"] for row in rows)
    expected = {"TCBIS_stop": 441, "campus_estimated_point": 20}
    if dict(counts) != expected:
        fail(f"unexpected location source counts: {dict(counts)}; expected {expected}")
    print("OK: location metadata (441 TCBIS stops + 20 campus-estimated points)")


def validate_archived_outputs() -> None:
    script = ROOT / "analysis" / "validate_raw_data.py"
    subprocess.run([sys.executable, str(script)], cwd=ROOT / "analysis", check=True)


def main() -> None:
    validate_required_files()
    validate_demand_workbook()
    validate_location_metadata()
    validate_archived_outputs()
    print("Package validation completed successfully.")


if __name__ == "__main__":
    main()
