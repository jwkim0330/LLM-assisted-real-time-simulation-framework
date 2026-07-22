from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def run(script: Path, *args: str) -> None:
    command = [sys.executable, str(script), *args]
    print("\n$ " + " ".join(command), flush=True)
    subprocess.run(command, cwd=ROOT, check=True)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate data, rebuild processed tables, and reproduce Figures 12-16."
    )
    parser.add_argument("--skip-preprocessing", action="store_true")
    parser.add_argument("--skip-figures", action="store_true")
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()

    run(ROOT / "validate_raw_data.py")
    if args.validate_only:
        return

    if not args.skip_preprocessing:
        run(ROOT / "preprocessing" / "prep_target_group.py")
        run(ROOT / "preprocessing" / "prep_total_group.py")
        run(ROOT / "preprocessing" / "prep_background_group.py")
        run(ROOT / "preprocessing" / "table_success_rate.py")
        run(ROOT / "preprocessing" / "table_target_delay_burden.py")

    if not args.skip_figures:
        for number in range(12, 17):
            run(ROOT / "figures" / "scripts" / f"figure{number}.py")

    print("\nReproduction pipeline completed successfully.")
    print(f"Processed data: {ROOT / 'data' / 'processed'}")
    print(f"Figures: {ROOT / 'figures' / 'output'}")


if __name__ == "__main__":
    main()
