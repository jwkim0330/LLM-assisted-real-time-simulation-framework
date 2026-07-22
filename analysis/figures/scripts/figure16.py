# -*- coding: utf-8 -*-
"""
Windows용 Figure 16 재현 코드

입력:
    preprocessed_background_group/seed_metrics_tidy.csv
또는
    preprocessed_background_group/seed_metrics_tidy_background.csv
또는
    seed_metrics_tidy.csv

출력:
    Figure 16. Paired seed-level comparison of background-passenger
    performance across the three scenarios..tiff
    Figure16_preview.png

설정:
    - 2 x 3 paired seed-level panels
    - Festival, Lunch, Holiday
    - Mean wait time / P95 wait time
    - Arial 우선 사용
    - 600 dpi
    - RGBA TIFF
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib import font_manager
from PIL import Image


DPI = 600
EXPECTED_WIDTH_PX = 4390
EXPECTED_HEIGHT_PX = 2949

SCENARIO_ORDER = ["Festival", "Lunch", "Holiday"]
CONDITION_ORDER = ["Uniform", "Poisson", "Synchronized"]

COLORS = {
    "Uniform": "#A9A9A9",
    "Poisson": "#696969",
    "Synchronized": "#000000",
}

LINE_COLOR = "#C7C7C7"
GRID_COLOR = "#E6E6E6"

OUTPUT_TIFF_NAME = (
    "Figure 16. Paired seed-level comparison of background-passenger "
    "performance across the three scenarios..tiff"
)
OUTPUT_PREVIEW_NAME = "Figure16_preview.png"


def select_windows_font() -> str:
    for candidate in ["Arial", "Liberation Sans", "DejaVu Sans"]:
        try:
            font_manager.findfont(candidate, fallback_to_default=False)
            return candidate
        except ValueError:
            continue
    raise RuntimeError(
        "Arial, Liberation Sans 또는 DejaVu Sans 폰트를 찾을 수 없습니다."
    )


def configure_matplotlib() -> str:
    selected_font = select_windows_font()

    plt.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": [selected_font],
            "axes.unicode_minus": False,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "font.size": 10,
            "axes.titlesize": 11,
            "axes.labelsize": 11,
            "xtick.labelsize": 9,
            "ytick.labelsize": 9,
            "legend.fontsize": 9,
            "savefig.facecolor": "white",
        }
    )
    return selected_font


def locate_metrics_csv(script_dir: Path, user_path: str | None) -> Path:
    """프로젝트 구조를 기준으로 입력 파일을 찾고, CLI 경로가 있으면 우선 사용한다."""
    if user_path:
        path = Path(user_path).expanduser().resolve()
        if not path.is_file():
            raise FileNotFoundError(f"지정한 CSV 파일이 없습니다: {path}")
        return path

    project_root = script_dir.parents[1]
    path = project_root / "data" / "processed" / "background" / "background_group_seed_metrics.csv"
    if not path.is_file():
        raise FileNotFoundError(f"입력 CSV를 찾지 못했습니다: {path}")
    return path


def load_background_metrics(csv_path: Path) -> pd.DataFrame:
    df = pd.read_csv(csv_path)

    rename_map = {}
    if "scenario" in df.columns and "Scenario" not in df.columns:
        rename_map["scenario"] = "Scenario"
    if "condition" in df.columns and "Condition" not in df.columns:
        rename_map["condition"] = "Condition"
    if "seed" in df.columns and "Seed" not in df.columns:
        rename_map["seed"] = "Seed"
    if "mean_wait" in df.columns and "MeanWait" not in df.columns:
        rename_map["mean_wait"] = "MeanWait"
    if "p95_wait" in df.columns and "P95Wait" not in df.columns:
        rename_map["p95_wait"] = "P95Wait"
    if "group" in df.columns and "Group" not in df.columns:
        rename_map["group"] = "Group"

    if rename_map:
        df = df.rename(columns=rename_map)

    required_columns = {
        "Scenario",
        "Condition",
        "Seed",
        "MeanWait",
        "P95Wait",
    }
    missing = required_columns.difference(df.columns)
    if missing:
        raise ValueError(
            "입력 CSV에 필요한 열이 없습니다: "
            + ", ".join(sorted(missing))
        )

    # Group 열이 있으면 Background 관련 행 우선 선택
    if "Group" in df.columns:
        group_series = df["Group"].astype(str).str.strip().str.lower()
        bg_mask = group_series.isin(
            {
                "background",
                "backgroundgroup",
                "background_group",
                "non-target",
                "nontarget",
                "others",
            }
        )
        if bg_mask.any():
            df = df.loc[bg_mask].copy()

    df["Scenario"] = pd.Categorical(
        df["Scenario"],
        categories=SCENARIO_ORDER,
        ordered=True,
    )
    df["Condition"] = pd.Categorical(
        df["Condition"],
        categories=CONDITION_ORDER,
        ordered=True,
    )

    df["MeanWait"] = pd.to_numeric(df["MeanWait"], errors="coerce")
    df["P95Wait"] = pd.to_numeric(df["P95Wait"], errors="coerce")

    df = df.dropna(
        subset=["Scenario", "Condition", "Seed", "MeanWait", "P95Wait"]
    ).copy()

    if df.empty:
        raise ValueError("사용 가능한 Background-group 데이터가 없습니다.")

    return df


def bootstrap_ci(
    values: np.ndarray,
    n_boot: int = 3000,
    alpha: float = 0.05,
    random_state: int = 42,
) -> tuple[float, float]:
    values = np.asarray(values, dtype=float)
    values = values[np.isfinite(values)]

    if values.size == 0:
        return np.nan, np.nan
    if values.size == 1:
        return float(values[0]), float(values[0])

    rng = np.random.default_rng(random_state)
    samples = rng.choice(
        values,
        size=(n_boot, values.size),
        replace=True,
    )
    medians = np.median(samples, axis=1)
    low = float(np.percentile(medians, 100 * (alpha / 2)))
    high = float(np.percentile(medians, 100 * (1 - alpha / 2)))
    return low, high


def style_axis(ax: plt.Axes) -> None:
    ax.grid(axis="y", color=GRID_COLOR, linewidth=0.7)
    ax.set_axisbelow(True)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


def plot_paired_seed_panel(
    ax: plt.Axes,
    data: pd.DataFrame,
    y_column: str,
    y_label: str,
    scenario_title: str,
) -> None:
    style_axis(ax)

    x_position = {condition: idx for idx, condition in enumerate(CONDITION_ORDER)}

    wide = data.pivot_table(
        index="Seed",
        columns="Condition",
        values=y_column,
        aggfunc="mean",
        observed=False,
    ).reindex(columns=CONDITION_ORDER)

    for _, row in wide.iterrows():
        xs = []
        ys = []
        for condition in CONDITION_ORDER:
            value = row.get(condition, np.nan)
            if pd.notna(value):
                xs.append(float(x_position[condition]))
                ys.append(float(value))
        if len(xs) >= 2:
            ax.plot(
                xs,
                ys,
                color=LINE_COLOR,
                linewidth=0.6,
                alpha=0.55,
                zorder=1,
            )

    jitter_rng = np.random.default_rng(42)

    for condition in CONDITION_ORDER:
        values = (
            data.loc[data["Condition"] == condition, y_column]
            .dropna()
            .to_numpy(dtype=float)
        )
        x = x_position[condition]

        jitter = jitter_rng.normal(loc=0.0, scale=0.03, size=values.size)

        ax.scatter(
            np.full(values.size, x, dtype=float) + jitter,
            values,
            s=10,
            color=COLORS[condition],
            alpha=0.80,
            edgecolor="none",
            zorder=2,
        )

        if values.size:
            median = float(np.median(values))
            ci_low, ci_high = bootstrap_ci(values)

            ax.plot(
                [x, x],
                [ci_low, ci_high],
                color="black",
                linewidth=1.2,
                zorder=3,
            )
            ax.scatter(
                [x],
                [median],
                s=24,
                color="white",
                edgecolor="black",
                linewidth=1.0,
                zorder=4,
            )

    ax.set_xticks(range(len(CONDITION_ORDER)))
    ax.set_xticklabels(CONDITION_ORDER, rotation=0, ha="center")
    ax.set_ylabel(y_label)
    ax.set_title(
        scenario_title,
        loc="center",
        fontsize=11,
        fontweight="normal",
    )


def add_panel_label(ax: plt.Axes, label: str) -> None:
    ax.text(
        -0.16, 1.08, label,
        transform=ax.transAxes,
        fontsize=12,
        fontweight="bold",
        ha="left",
        va="top",
        clip_on=False,
    )


def make_figure16(
    background_df: pd.DataFrame,
    output_tiff: Path,
    output_preview: Path,
) -> None:
    fig, axes = plt.subplots(
        2,
        3,
        figsize=(7.2, 4.8),
        constrained_layout=True,
        dpi=DPI,
    )

    panel_labels = ["A", "B", "C", "D", "E", "F"]

    for column, scenario in enumerate(SCENARIO_ORDER):
        subset = background_df.loc[
            background_df["Scenario"].astype(str) == scenario
        ].copy()

        plot_paired_seed_panel(
            ax=axes[0, column],
            data=subset,
            y_column="MeanWait",
            y_label="Mean wait time (s)" if column == 0 else "",
            scenario_title=scenario,
        )
        add_panel_label(axes[0, column], panel_labels[column])

        plot_paired_seed_panel(
            ax=axes[1, column],
            data=subset,
            y_column="P95Wait",
            y_label="P95 wait time (s)" if column == 0 else "",
            scenario_title=scenario,
        )
        add_panel_label(axes[1, column], panel_labels[column + 3])

    fig.savefig(
        output_tiff,
        dpi=DPI,
        format="tiff",
        bbox_inches="tight",
        facecolor="white",
    )

    fig.savefig(
        output_preview,
        dpi=300,
        format="png",
        bbox_inches="tight",
        facecolor="white",
    )

    plt.close(fig)


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Windows에서 최종 Figure 16을 재현합니다."
    )
    parser.add_argument(
        "--metrics_csv",
        type=str,
        default=None,
        help="Background-group seed metrics CSV의 전체 경로",
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default=None,
        help="출력 폴더. 생략하면 plos_figures_final 사용",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_arguments()
    script_dir = Path(__file__).resolve().parent

    selected_font = configure_matplotlib()
    metrics_csv = locate_metrics_csv(script_dir, args.metrics_csv)

    output_dir = (
        Path(args.output_dir).expanduser().resolve()
        if args.output_dir
        else script_dir.parents[1] / "figures" / "output"
    )
    output_dir.mkdir(parents=True, exist_ok=True)

    output_tiff = output_dir / OUTPUT_TIFF_NAME
    output_preview = output_dir / OUTPUT_PREVIEW_NAME

    background_df = load_background_metrics(metrics_csv)
    make_figure16(background_df, output_tiff, output_preview)

    with Image.open(output_tiff) as image:
        width, height = image.size
        mode = image.mode
        dpi = image.info.get("dpi")

    print(f"사용 폰트: {selected_font}")
    print(f"입력 데이터: {metrics_csv}")
    print(f"TIFF 저장: {output_tiff}")
    print(f"PNG 저장: {output_preview}")
    print(f"TIFF 정보: {width} x {height} px, mode={mode}, dpi={dpi}")

    if (width, height) != (EXPECTED_WIDTH_PX, EXPECTED_HEIGHT_PX):
        print(
            "주의: Matplotlib/폰트 버전 차이로 최종본의 "
            f"{EXPECTED_WIDTH_PX} x {EXPECTED_HEIGHT_PX} px와 "
            "몇 픽셀 차이가 날 수 있습니다."
        )


if __name__ == "__main__":
    main()