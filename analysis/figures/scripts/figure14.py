# -*- coding: utf-8 -*-
"""
Windows용 Figure 14 재현 코드

입력:
    preprocessed_target10/passenger_level_tidy.csv

출력:
    Figure 14. Empirical cumulative distribution functions of waiting
    times for the target passenger group..tiff
    Figure14_preview.png
    Figure14_TargetGroup_Wait_ECDF_summary.csv

최종 Figure 설정:
    - Festival, Lunch, Holiday 3개 패널
    - Target passenger group의 성공 승객 WaitTime을 seed 전체에서 통합
    - Uniform / Poisson / Synchronized ECDF
    - 4389 x 1569 px
    - 600 dpi
    - RGBA 무압축 TIFF
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

# PowerShell에서 GUI 창 없이 파일만 저장
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib import font_manager
from PIL import Image


DPI = 600
CANVAS_WIDTH_PX = 4389
CANVAS_HEIGHT_PX = 1569

SCENARIO_ORDER = ["Festival", "Lunch", "Holiday"]
CONDITION_ORDER = ["Uniform", "Poisson", "Synchronized"]

COLORS = {
    "Uniform": "#A9A9A9",
    "Poisson": "#696969",
    "Synchronized": "#000000",
}

LINE_STYLES = {
    "Uniform": "-",
    "Poisson": "--",
    "Synchronized": "-",
}

OUTPUT_TIFF_NAME = (
    "Figure 14. Empirical cumulative distribution functions of waiting "
    "times for the target passenger group..tiff"
)
OUTPUT_PREVIEW_NAME = "Figure14_preview.png"
OUTPUT_SUMMARY_NAME = "Figure14_TargetGroup_Wait_ECDF_summary.csv"


def select_font() -> str:
    """Windows에서는 Arial을 우선 사용한다."""
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
    selected_font = select_font()

    plt.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": [selected_font],
            "axes.unicode_minus": False,
            "font.size": 9,
            "axes.titlesize": 10,
            "axes.labelsize": 10,
            "xtick.labelsize": 8,
            "ytick.labelsize": 8,
            "legend.fontsize": 8,
            "savefig.facecolor": "white",
        }
    )
    return selected_font


def locate_passenger_csv(script_dir: Path, user_path: str | None) -> Path:
    """프로젝트 구조를 기준으로 입력 파일을 찾고, CLI 경로가 있으면 우선 사용한다."""
    if user_path:
        path = Path(user_path).expanduser().resolve()
        if not path.is_file():
            raise FileNotFoundError(f"지정한 CSV 파일이 없습니다: {path}")
        return path

    project_root = script_dir.parents[1]
    path = project_root / "data" / "processed" / "target" / "passenger_level_tidy.csv"
    if not path.is_file():
        raise FileNotFoundError(f"입력 CSV를 찾지 못했습니다: {path}")
    return path


def to_boolean(series: pd.Series) -> pd.Series:
    """bool 또는 문자열로 저장된 Success 열을 모두 처리한다."""
    if pd.api.types.is_bool_dtype(series):
        return series.fillna(False)

    return (
        series.astype(str)
        .str.strip()
        .str.lower()
        .isin({"true", "1", "yes", "y"})
    )


def load_target_waits(csv_path: Path) -> pd.DataFrame:
    df = pd.read_csv(csv_path)

    required_columns = {
        "Scenario",
        "Condition",
        "PassengerGroup",
        "Success",
        "WaitTime",
    }
    missing = required_columns.difference(df.columns)
    if missing:
        raise ValueError(
            "입력 CSV에 필요한 열이 없습니다: "
            + ", ".join(sorted(missing))
        )

    df["WaitTime"] = pd.to_numeric(df["WaitTime"], errors="coerce")
    success = to_boolean(df["Success"])

    target = df.loc[
        df["PassengerGroup"].astype(str).str.strip().eq("Target")
        & success
        & df["WaitTime"].notna()
        & np.isfinite(df["WaitTime"])
    ].copy()

    target = target.loc[
        target["Scenario"].isin(SCENARIO_ORDER)
        & target["Condition"].isin(CONDITION_ORDER)
    ].copy()

    if target.empty:
        raise ValueError(
            "성공한 Target passenger의 WaitTime 데이터가 없습니다."
        )

    return target


def ecdf(values: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    values = np.asarray(values, dtype=float)
    values = values[np.isfinite(values)]

    if values.size == 0:
        return np.array([]), np.array([])

    x = np.sort(values)
    y = np.arange(1, values.size + 1, dtype=float) / values.size
    return x, y


def gini(values: np.ndarray) -> float:
    values = np.asarray(values, dtype=float)
    values = values[np.isfinite(values)]

    if values.size == 0:
        return float("nan")

    minimum = float(np.min(values))
    if minimum < 0:
        values = values - minimum

    total = float(np.sum(values))
    if total == 0:
        return 0.0

    values = np.sort(values)
    n = values.size
    index = np.arange(1, n + 1, dtype=float)

    return float(
        (2.0 * np.sum(index * values) / (n * total))
        - ((n + 1.0) / n)
    )


def build_summary(target: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []

    for scenario in SCENARIO_ORDER:
        for condition in CONDITION_ORDER:
            values = target.loc[
                (target["Scenario"] == scenario)
                & (target["Condition"] == condition),
                "WaitTime",
            ].to_numpy(dtype=float)

            rows.append(
                {
                    "Scenario": scenario,
                    "Condition": condition,
                    "N_target_observations": int(values.size),
                    "MeanWait": float(np.mean(values)),
                    "MedianWait": float(np.median(values)),
                    "P95Wait": float(np.quantile(values, 0.95)),
                    "Gini": gini(values),
                }
            )

    return pd.DataFrame(rows)


def style_axis(ax: plt.Axes, index: int) -> None:
    ax.set_ylim(0.0, 1.02)
    ax.set_yticks(np.arange(0.0, 1.01, 0.2))

    if index == 0:
        ax.set_xticks(np.arange(0, 901, 200))
    elif index == 1:
        ax.set_xticks(np.arange(0, 1001, 250))
    else:
        ax.set_xticks(np.arange(0, 901, 200))

    ax.grid(
        True,
        which="major",
        color="#E6E6E6",
        linewidth=0.7,
    )
    ax.set_axisbelow(True)

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    ax.tick_params(
        axis="both",
        which="major",
        labelsize=8,
    )


def make_figure14(
    target: pd.DataFrame,
    output_tiff: Path,
    output_preview: Path,
) -> None:
    fig = plt.figure(
        figsize=(
            CANVAS_WIDTH_PX / DPI,
            CANVAS_HEIGHT_PX / DPI,
        ),
        dpi=DPI,
        facecolor="white",
    )

    # 최종 TIFF에서 측정한 고정 패널 좌표
    axes_left_px = [295, 1717, 3140]
    axes_right_px = [1488, 2911, 4333]
    axes_top_px = 163
    axes_bottom_px = 1300

    axes: list[plt.Axes] = []

    for left_px, right_px in zip(
        axes_left_px,
        axes_right_px,
    ):
        ax = fig.add_axes(
            [
                left_px / CANVAS_WIDTH_PX,
                (CANVAS_HEIGHT_PX - axes_bottom_px)
                / CANVAS_HEIGHT_PX,
                (right_px - left_px) / CANVAS_WIDTH_PX,
                (axes_bottom_px - axes_top_px)
                / CANVAS_HEIGHT_PX,
            ]
        )
        axes.append(ax)

    for index, scenario in enumerate(SCENARIO_ORDER):
        ax = axes[index]

        for condition in CONDITION_ORDER:
            values = target.loc[
                (target["Scenario"] == scenario)
                & (target["Condition"] == condition),
                "WaitTime",
            ].to_numpy(dtype=float)

            x, y = ecdf(values)

            ax.step(
                x,
                y,
                where="post",
                color=COLORS[condition],
                linestyle=LINE_STYLES[condition],
                linewidth=1.4,
                label=condition,
                zorder=3,
            )

        style_axis(ax, index)

        ax.set_title(
            scenario,
            fontsize=10,
            fontweight="normal",
            pad=6,
        )
        ax.set_xlabel(
            "Waiting time (s)",
            fontsize=10,
            labelpad=4,
        )

        if index == 0:
            ax.set_ylabel(
                "ECDF",
                fontsize=10,
                labelpad=4,
            )

        ax.text(
            -0.155,
            1.055,
            chr(ord("A") + index),
            transform=ax.transAxes,
            fontsize=12,
            fontweight="bold",
            ha="left",
            va="top",
            clip_on=False,
        )

        if index == 2:
            ax.legend(
                loc="lower right",
                frameon=False,
                fontsize=8,
                handlelength=2.0,
                handletextpad=0.8,
                borderaxespad=0.5,
            )

    # bbox_inches="tight"를 사용하지 않아 최종 픽셀 크기를 고정한다.
    fig.savefig(
        output_tiff,
        dpi=DPI,
        format="tiff",
        facecolor="white",
    )

    fig.savefig(
        output_preview,
        dpi=300,
        format="png",
        facecolor="white",
    )

    plt.close(fig)


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Windows에서 최종 Figure 14 ECDF를 재현합니다."
    )
    parser.add_argument(
        "--passenger_csv",
        type=str,
        default=None,
        help="passenger_level_tidy.csv의 전체 경로",
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
    passenger_csv = locate_passenger_csv(
        script_dir,
        args.passenger_csv,
    )

    output_dir = (
        Path(args.output_dir).expanduser().resolve()
        if args.output_dir
        else script_dir.parents[1] / "figures" / "output"
    )
    output_dir.mkdir(parents=True, exist_ok=True)

    output_tiff = output_dir / OUTPUT_TIFF_NAME
    output_preview = output_dir / OUTPUT_PREVIEW_NAME
    output_summary = output_dir / OUTPUT_SUMMARY_NAME

    target = load_target_waits(passenger_csv)
    summary = build_summary(target)

    make_figure14(
        target=target,
        output_tiff=output_tiff,
        output_preview=output_preview,
    )
    summary.to_csv(
        output_summary,
        index=False,
        encoding="utf-8-sig",
    )

    with Image.open(output_tiff) as image:
        width, height = image.size
        mode = image.mode
        dpi = image.info.get("dpi")
        compression = image.info.get("compression")

    print(f"사용 폰트: {selected_font}")
    print(f"입력 데이터: {passenger_csv}")
    print(f"TIFF 저장: {output_tiff}")
    print(f"PNG 저장: {output_preview}")
    print(f"요약 CSV 저장: {output_summary}")
    print(
        "TIFF 정보: "
        f"{width} x {height} px, "
        f"mode={mode}, dpi={dpi}, "
        f"compression={compression}"
    )

    if (width, height) != (
        CANVAS_WIDTH_PX,
        CANVAS_HEIGHT_PX,
    ):
        raise RuntimeError(
            "출력 크기가 최종본과 다릅니다: "
            f"{width} x {height} px"
        )


if __name__ == "__main__":
    main()