from __future__ import annotations

import argparse
import shutil
from pathlib import Path

SCENARIOS = ("Festival", "Lunch", "Holiday")
CONDITIONS = ("HILS_BURST", "MATH_UNIFORM", "MATH_POISSON")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Copy simulation CSV outputs into the analysis raw-data layout."
    )
    parser.add_argument(
        "--source",
        type=Path,
        default=Path(__file__).resolve().parent / "results_experiment",
    )
    parser.add_argument(
        "--analysis-dir",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "analysis",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace existing CSV files with the same names.",
    )
    args = parser.parse_args()

    source = args.source.expanduser().resolve()
    destination_root = args.analysis_dir.expanduser().resolve() / "data" / "raw"

    copied = 0
    skipped = 0
    for scenario in SCENARIOS:
        for condition in CONDITIONS:
            src_dir = source / scenario / condition
            if not src_dir.is_dir():
                raise FileNotFoundError(f"Missing simulation output directory: {src_dir}")

            dst_dir = destination_root / scenario / condition
            dst_dir.mkdir(parents=True, exist_ok=True)

            for src_file in sorted(src_dir.glob("*.csv")):
                dst_file = dst_dir / src_file.name
                if dst_file.exists() and not args.overwrite:
                    skipped += 1
                    continue
                shutil.copy2(src_file, dst_file)
                copied += 1

    print(f"Copied {copied} files; skipped {skipped} existing files.")
    print(f"Analysis raw-data root: {destination_root}")


if __name__ == "__main__":
    main()
