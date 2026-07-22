# -*- coding: utf-8 -*-
"""
Windows용 Figure 13 재현 코드

입력:
    preprocessed_target10/seed_metrics_tidy.csv

출력:
    Figure 13. Paired seed-level comparison of target-passenger
    performance across the three scenarios..tiff
    Figure13_preview.png

최종 Figure 설정:
    - 2 x 3 paired seed-level panels
    - Festival, Lunch, Holiday
    - Mean wait time / Gini coefficient
    - Arial 우선 사용
    - 600 dpi, uncompressed RGBA TIFF
    - 최종 이미지 기준 4390 x 2949 px
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

# PowerShell에서 GUI 창 없이 저장되도록 설정
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
    "Figure 13. Paired seed-level comparison of target-passenger "
    "performance across the three scenarios..tiff"
)
OUTPUT_PREVIEW_NAME = "Figure13_preview.png"


def select_windows_font() -> str:
    """Windows에서는 Arial을 우선 사용하고, 없으면 대체 폰트를 선택한다."""
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
    path = project_root / "data" / "processed" / "target" / "seed_metrics_tidy.csv"
    if not path.is_file():
        raise FileNotFoundError(f"입력 CSV를 찾지 못했습니다: {path}")
    return path


def load_target_metrics(csv_path: Path) -> pd.DataFrame:
    df = pd.read_csv(csv_path)

    required_columns = {
        "Scenario",
        "Condition",
        "Seed",
        "Group",
        "MeanWait",
        "Gini",
    }
    missing = required_columns.difference(df.columns)
    if missing:
        raise ValueError(
            "입력 CSV에 필요한 열이 없습니다: "
            + ", ".join(sorted(missing))
        )

    target = df.loc[df["Group"].astype(str) == "Target"].copy()
    if target.empty:
        raise ValueError("Group='Target'인 데이터가 없습니다.")

    target["Scenario"] = pd.Categorical(
        target["Scenario"],
        categories=SCENARIO_ORDER,
        ordered=True,
    )
    target["Condition"] = pd.Categorical(
        target["Condition"],
        categories=CONDITION_ORDER,
        ordered=True,
    )

    target = target.dropna(
        subset=["Scenario", "Condition", "Seed", "MeanWait", "Gini"]
    )

    return target


def bootstrap_ci(
    values: np.ndarray,
    n_boot: int = 3000,
    alpha: float = 0.05,
    random_state: int = 42,
) -> tuple[float, float]:
    """중앙값의 percentile bootstrap 95% CI."""
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
    ax.grid(
        axis="y",
        color=GRID_COLOR,
        linewidth=0.7,
    )
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

    x_position = {
        condition: index
        for index, condition in enumerate(CONDITION_ORDER)
    }

    # 같은 seed의 세 조건을 연결
    wide = data.pivot_table(
        index="Seed",
        columns="Condition",
        values=y_column,
        aggfunc="mean",
        observed=False,
    ).reindex(columns=CONDITION_ORDER)

    for _, row in wide.iterrows():
        xs: list[float] = []
        ys: list[float] = []

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

    # 각 조건의 seed-level 점과 중앙값·bootstrap CI
    jitter_rng = np.random.default_rng(42)

    for condition in CONDITION_ORDER:
        values = (
            data.loc[data["Condition"] == condition, y_column]
            .dropna()
            .to_numpy(dtype=float)
        )
        x = x_position[condition]

        jitter = jitter_rng.normal(
            loc=0.0,
            scale=0.03,
            size=values.size,
        )

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
    ax.set_xticklabels(
        CONDITION_ORDER,
        rotation=0,
        ha="center",
    )
    ax.set_ylabel(y_label)

    # 최종본은 상단과 하단 패널 모두 시나리오 제목을 표시함
    ax.set_title(
        scenario_title,
        loc="center",
        fontsize=11,
        fontweight="normal",
    )


def add_panel_label(ax: plt.Axes, label: str) -> None:
    # 중앙 시나리오 제목과 독립적으로 좌측 패널 문자를 배치
    ax.set_title(
        label,
        loc="left",
        fontsize=12,
        fontweight="bold",
    )


def make_figure13(
    target_df: pd.DataFrame,
    output_tiff: Path,
    output_preview: Path,
) -> None:
    # 이 크기와 tight bounding box 조합이 최종본 4390 x 2949 px에 대응함.
    fig, axes = plt.subplots(
        2,
        3,
        figsize=(7.2, 4.8),
        constrained_layout=True,
        dpi=DPI,
    )

    panel_labels = ["A", "B", "C", "D", "E", "F"]

    for column, scenario in enumerate(SCENARIO_ORDER):
        subset = target_df.loc[
            target_df["Scenario"].astype(str) == scenario
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
            y_column="Gini",
            y_label="Gini coefficient" if column == 0 else "",
            scenario_title=scenario,
        )
        add_panel_label(axes[1, column], panel_labels[column + 3])

    # 최종 제출본: 600 dpi, 무압축 RGBA TIFF
    fig.savefig(
        output_tiff,
        dpi=DPI,
        format="tiff",
        bbox_inches="tight",
        facecolor="white",
    )

    # 화면 확인용 PNG
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
        description="Windows에서 최종 Figure 13을 재현합니다."
    )
    parser.add_argument(
        "--metrics_csv",
        type=str,
        default=None,
        help="seed_metrics_tidy.csv의 전체 경로",
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default=None,
        help="출력 폴더. 생략하면 plos_figures_final 폴더를 사용",
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

    target_df = load_target_metrics(metrics_csv)
    make_figure13(target_df, output_tiff, output_preview)

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
            "주의: Matplotlib 또는 폰트 버전 차이로 최종본의 "
            f"{EXPECTED_WIDTH_PX} x {EXPECTED_HEIGHT_PX} px와 "
            "몇 픽셀 차이가 날 수 있습니다."
        )


if __name__ == "__main__":
    main()