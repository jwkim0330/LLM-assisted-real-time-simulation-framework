from __future__ import annotations

import argparse
import os
import time
from pathlib import Path
from typing import Iterable

from Environment.EnvironmentLoader import EnvironmentLoader
from Models.MobilitySim_model import MobilitySim_model
from SimulationEngine.SimulationEngine import SimulationEngine

BASE_DIR = Path(__file__).resolve().parent
JSON_DIR = BASE_DIR / "JSON"
CONFIG_FILES = ["map_graph_with_vectors", "passengerInfo", "shuttleInfo", "setup"]

SCENARIOS = {
    "FESTIVAL": "Festival",
    "LUNCH": "Lunch",
    "HOLIDAY": "Holiday",
}
CONDITIONS = (
    "HILS_BURST",
    "MATH_UNIFORM",
    "MATH_POISSON",
)


def parse_choice_list(raw: str, allowed: Iterable[str], label: str) -> list[str]:
    allowed_set = set(allowed)
    if raw.strip().lower() == "all":
        return list(allowed)

    values = [item.strip().upper() for item in raw.split(",") if item.strip()]
    invalid = [item for item in values if item not in allowed_set]
    if invalid:
        raise argparse.ArgumentTypeError(
            f"Invalid {label}: {invalid}. Allowed values: {sorted(allowed_set)}"
        )
    if not values:
        raise argparse.ArgumentTypeError(f"At least one {label} must be selected.")
    return values


def build_parser(default_end_seed: int) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run the DRT simulation for selected scenarios, demand conditions, "
            "and random seeds."
        )
    )
    parser.add_argument(
        "--scenarios",
        default="all",
        help="Comma-separated scenario names or 'all': FESTIVAL,LUNCH,HOLIDAY",
    )
    parser.add_argument(
        "--conditions",
        default="all",
        help=(
            "Comma-separated condition names or 'all': "
            "HILS_BURST,MATH_UNIFORM,MATH_POISSON"
        ),
    )
    parser.add_argument("--start-seed", type=int, default=1)
    parser.add_argument("--end-seed", type=int, default=default_end_seed)
    parser.add_argument("--max-time", type=float, default=3600.0)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=BASE_DIR / "results_experiment",
        help="Root directory for generated CSV files.",
    )
    return parser


def main() -> None:
    os.chdir(BASE_DIR)

    initial_config = EnvironmentLoader(str(JSON_DIR) + os.sep, CONFIG_FILES).getConfiguration()
    simulation_mode = initial_config.getConfiguration("simulationMode")
    if simulation_mode is not True:
        raise RuntimeError('JSON/setup.json must contain "simulationMode": true.')

    monte_carlo = int(initial_config.getConfiguration("monteCarlo"))
    args = build_parser(monte_carlo).parse_args()

    scenarios = parse_choice_list(args.scenarios, SCENARIOS, "scenario")
    conditions = parse_choice_list(args.conditions, CONDITIONS, "condition")

    if args.start_seed < 1 or args.end_seed < args.start_seed:
        raise ValueError("Seeds must satisfy 1 <= start-seed <= end-seed.")
    if args.max_time <= 0:
        raise ValueError("--max-time must be positive.")

    num_shuttles = initial_config.getConfiguration("numShuttles")
    render_time = initial_config.getConfiguration("renderTime")
    is_shuttle_change = initial_config.getConfiguration("isShuttleChange")
    gen_end_time = initial_config.getConfiguration("genEndTime")
    ed_service_rate = initial_config.getConfiguration("EDServiceRateLst")[0]
    passenger_percent = initial_config.getConfiguration("psgrPercentLst")[0]

    args.output_dir = args.output_dir.expanduser().resolve()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    total_start = time.time()
    total_runs = len(scenarios) * len(conditions) * (
        args.end_seed - args.start_seed + 1
    )
    completed = 0

    for scenario in scenarios:
        os.environ["TARGET_SCENARIO"] = scenario

        for condition in conditions:
            os.environ["TARGET_DIST"] = condition

            for seed in range(args.start_seed, args.end_seed + 1):
                os.environ["CURRENT_SEED"] = str(seed)
                fresh_config = EnvironmentLoader(
                    str(JSON_DIR) + os.sep, CONFIG_FILES
                ).getConfiguration()

                model = MobilitySim_model(
                    fresh_config,
                    str(JSON_DIR) + os.sep,
                    seed,
                    args.end_seed,
                    None,
                    render_time,
                    num_shuttles,
                    num_shuttles,
                    is_shuttle_change,
                    gen_end_time,
                    ed_service_rate,
                    passenger_percent,
                    simulation_mode,
                )

                engine = SimulationEngine()
                engine.setOutmostModel(model)

                run_start = time.time()
                completed += 1
                print(
                    f"[{completed}/{total_runs}] scenario={scenario} "
                    f"condition={condition} seed={seed}"
                )
                engine.run(maxTime=args.max_time)

                save_dir = args.output_dir / SCENARIOS[scenario] / condition
                model.objGenerator.kpi_saver.save_and_clear(
                    output_dir=str(save_dir),
                    seed_num=seed,
                )
                print(
                    f"Saved: {save_dir} "
                    f"(elapsed={time.time() - run_start:.2f}s)"
                )

    print(
        f"Completed {total_runs} runs in "
        f"{(time.time() - total_start) / 60:.2f} minutes."
    )


if __name__ == "__main__":
    main()
