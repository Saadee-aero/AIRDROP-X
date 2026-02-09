"""
Reusable plotting functions. Military HUD style. No engine or advisory calls.
"""

import numpy as np
import matplotlib.pyplot as plt

_PANEL = "#0f120f"
_ACCENT = "#00ff41"
_ACCENT_DIM = "#1a4d1a"
_TARGET_RING = "#00ff41"
_CEP_RING = "#4a7c4a"
_SCATTER = "#00ff41"
_LABEL = "#6b8e6b"
_GRID = "#1a3a1a"
_BORDER = "#2a3a2a"


def plot_impact_dispersion(
    ax,
    impact_points,
    target_position,
    target_radius,
    cep50=None,
):
    impact_points = np.asarray(impact_points, dtype=float)
    target_position = np.asarray(target_position, dtype=float).reshape(2)
    r_target = float(target_radius) if target_radius is not None else 0.0
    r_cep = float(cep50) if (cep50 is not None and cep50 > 0) else 0.0
    r_max = max(r_target, r_cep)

    ax.set_facecolor(_PANEL)
    ax.tick_params(colors=_LABEL)
    ax.xaxis.label.set_color(_LABEL)
    ax.yaxis.label.set_color(_LABEL)
    for spine in ax.spines.values():
        spine.set_color(_BORDER)

    ax.scatter(impact_points[:, 0], impact_points[:, 1], color=_SCATTER, alpha=0.35, s=10, edgecolors="none", clip_on=True)
    ax.add_patch(
        plt.Circle(target_position, target_radius, color=_TARGET_RING, fill=False, linewidth=1.5, clip_on=True)
    )
    ax.scatter(target_position[0], target_position[1], color=_TARGET_RING, s=40, zorder=5, edgecolors=_PANEL, linewidths=0.5, clip_on=True)
    if cep50 is not None and cep50 > 0:
        ax.add_patch(
            plt.Circle(target_position, cep50, color=_CEP_RING, fill=False, linestyle="--", linewidth=1, clip_on=True)
        )

    x_min = min(impact_points[:, 0].min(), target_position[0] - r_max)
    x_max = max(impact_points[:, 0].max(), target_position[0] + r_max)
    y_min = min(impact_points[:, 1].min(), target_position[1] - r_max)
    y_max = max(impact_points[:, 1].max(), target_position[1] + r_max)
    dx = max(x_max - x_min, 1e-6)
    dy = max(y_max - y_min, 1e-6)
    margin = 0.08 * max(dx, dy)
    half = max(dx, dy) * 0.5 + margin
    cx = (x_min + x_max) * 0.5
    cy = (y_min + y_max) * 0.5
    ax.set_xlim(cx - half, cx + half)
    ax.set_ylim(cy - half, cy + half)

    ax.set_xlabel("X (m)", labelpad=0)
    ax.set_ylabel("Y (m)", labelpad=0)
    ax.tick_params(axis="both", pad=2)
    ax.axis("equal")
    ax.grid(True, color=_GRID, alpha=0.6, linestyle="-")


def plot_sensitivity(ax, x_values, y_values, x_label, y_label, title=None):
    x_values = np.asarray(x_values, dtype=float)
    y_values = np.asarray(y_values, dtype=float)
    ax.set_facecolor(_PANEL)
    ax.tick_params(colors=_LABEL)
    ax.plot(x_values, y_values, color=_ACCENT, clip_on=True)
    ax.margins(x=0.04, y=0.04)
    ax.set_xlabel(x_label, color=_LABEL)
    ax.set_ylabel(y_label, color=_LABEL)
    ax.grid(True, color=_GRID, alpha=0.6)
    if title is not None:
        ax.set_title(title, color=_LABEL)
    for spine in ax.spines.values():
        spine.set_color(_BORDER)


def create_figure_axes(nrows=1, ncols=1, figsize=(6, 6)):
    fig, ax = plt.subplots(nrows, ncols, figsize=figsize)
    if nrows == 1 and ncols == 1:
        return fig, ax
    return fig, ax
