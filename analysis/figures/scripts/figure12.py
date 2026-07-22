# -*- coding: utf-8 -*-
"""Reproduce the final Figure 12 TIFF.

Windows-compatible font: Arial preferred
Output: 4499 x 3422 px, 600 dpi, uncompressed RGBA TIFF
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib import font_manager
from matplotlib.lines import Line2D


# -----------------------------------------------------------------------------
# Output settings
# -----------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parents[1]
OUTPUT_DIR = PROJECT_ROOT / "figures" / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

DPI = 600
CANVAS_WIDTH_PX = 4499
CANVAS_HEIGHT_PX = 3422
OUTPUT_TIFF = OUTPUT_DIR / (
    "Figure 12. Temporal profiles of the injected target demand "
    "under the three experimental conditions..tiff"
)
OUTPUT_PREVIEW = OUTPUT_DIR / "Figure12_preview.png"

# Windows-compatible font selection.
# Arial is normally preinstalled on Windows. If unavailable, Liberation Sans
# or DejaVu Sans is selected automatically.
font_candidates = ["Arial", "Liberation Sans", "DejaVu Sans"]
selected_font = None

for candidate in font_candidates:
    try:
        font_manager.findfont(candidate, fallback_to_default=False)
        selected_font = candidate
        break
    except ValueError:
        continue

if selected_font is None:
    raise RuntimeError("No compatible sans-serif font was found.")

plt.rcParams.update(
    {
        "font.family": "sans-serif",
        "font.sans-serif": [selected_font],
        "axes.unicode_minus": False,
        "savefig.facecolor": "white",
    }
)

print(f"Using font: {selected_font}")

# -----------------------------------------------------------------------------
# Experimental demand-injection times
# -----------------------------------------------------------------------------
synchronized_times = np.full(10, 1500.0)

uniform_times = np.array(
    [1500, 1518, 1538, 1560, 1590, 1620, 1650, 1680, 1710, 1740],
    dtype=float,
)

poisson_times = np.array(
    [1500, 1514, 1537, 1594, 1620, 1622, 1627, 1672, 1672, 1802],
    dtype=float,
)


def cumulative_step(times: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Return sorted injection times and cumulative request counts."""
    x = np.sort(np.asarray(times, dtype=float))
    y = np.arange(1, x.size + 1)
    return x, y


# -----------------------------------------------------------------------------
# Figure construction
# -----------------------------------------------------------------------------
WHITE = "#FFFFFF"
TEXT = "#333333"
BLACK = "#000000"
DARK_GRAY = "#4D4D4D"
MID_GRAY = "#808080"

fig = plt.figure(
    figsize=(CANVAS_WIDTH_PX / DPI, CANVAS_HEIGHT_PX / DPI),
    dpi=DPI,
    facecolor=WHITE,
)

# Fixed pixel geometry from the final submitted TIFF.
# Data-coordinate axes rectangle:
# left=388 px, right=4319 px, top=297 px, bottom=3055 px.
left = 388 / CANVAS_WIDTH_PX
right = 4319 / CANVAS_WIDTH_PX
bottom = 1 - (3055 / CANVAS_HEIGHT_PX)
top = 1 - (297 / CANVAS_HEIGHT_PX)
ax = fig.add_axes([left, bottom, right - left, top - bottom])
ax.set_facecolor(WHITE)

# Synchronized demand: all ten requests are injected at t=1500 s.
ax.vlines(
    synchronized_times[0],
    ymin=0,
    ymax=synchronized_times.size,
    color=BLACK,
    linewidth=3.0,
    zorder=4,
)

x_poisson, y_poisson = cumulative_step(poisson_times)
x_uniform, y_uniform = cumulative_step(uniform_times)

ax.step(
    x_poisson,
    y_poisson,
    where="post",
    color=DARK_GRAY,
    linewidth=2.8,
    linestyle="--",
    zorder=3,
)
ax.step(
    x_uniform,
    y_uniform,
    where="post",
    color=MID_GRAY,
    linewidth=2.8,
    linestyle=":",
    zorder=2,
)

# Axes and labels
ax.set_xlim(1450, 1850)
ax.set_ylim(0, 10.5)
ax.set_xticks(np.arange(1450, 1851, 50))
ax.set_yticks(np.arange(0, 11, 2))

ax.set_title(
    "Temporal Injection Profile (Target N=10)",
    fontsize=16.98,
    fontweight="bold",
    color=TEXT,
    pad=16.24,
)
ax.set_xlabel(
    "Simulation Time (s)",
    fontsize=15,
    fontweight="bold",
    color=TEXT,
    labelpad=3.75,
)
ax.set_ylabel(
    "Cumulative Target Requests",
    fontsize=15,
    fontweight="bold",
    color=TEXT,
)

for spine_name in ("top", "right"):
    ax.spines[spine_name].set_visible(False)

for spine_name in ("left", "bottom"):
    ax.spines[spine_name].set_linewidth(1.2)
    ax.spines[spine_name].set_color(TEXT)

ax.tick_params(
    axis="both",
    which="major",
    labelsize=13,
    colors=TEXT,
)

legend_handles = [
    Line2D(
        [0],
        [0],
        color=BLACK,
        linewidth=3.0,
        linestyle="-",
        label="Synchronized",
    ),
    Line2D(
        [0],
        [0],
        color=DARK_GRAY,
        linewidth=2.8,
        linestyle="--",
        label="Poisson",
    ),
    Line2D(
        [0],
        [0],
        color=MID_GRAY,
        linewidth=2.8,
        linestyle=":",
        label="Uniform",
    ),
]

legend = ax.legend(
    handles=legend_handles,
    title="Demand Model",
    loc="lower right",
    bbox_to_anchor=(0.99949, -0.00145),
    frameon=False,
    fontsize=13,
    title_fontsize=16,
)
for text in legend.get_texts():
    text.set_color(TEXT)
legend.get_title().set_color(TEXT)

# Do not use tight_layout or bbox_inches='tight': the submitted TIFF has a
# fixed 4499 x 3422 pixel canvas and fixed axes coordinates.
fig.savefig(
    OUTPUT_TIFF,
    dpi=DPI,
    format="tiff",
    facecolor=WHITE,
)
fig.savefig(
    OUTPUT_PREVIEW,
    dpi=DPI,
    format="png",
    facecolor=WHITE,
)
plt.close(fig)

print(f"Saved: {OUTPUT_TIFF.resolve()}")
print(f"Saved: {OUTPUT_PREVIEW.resolve()}")