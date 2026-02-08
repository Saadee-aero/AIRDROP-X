"""
Mission Overview tab. Command-and-control: decision banner, key metrics, target view.
Receives precomputed data only; no computation.
"""

import numpy as np
import matplotlib.pyplot as plt

_BG = "#0a0c0a"
_PANEL = "#0f120f"
_GREEN = "#00ff41"
_RED = "#ff3333"
_LABEL = "#6b8e6b"
_TEXT = "#c0d0c0"
_BORDER = "#2a3a2a"
_SCATTER = "#00ff41"
_CEP = "#4a7c4a"
_MEAN = "#ffffff"


def render(
    ax,
    decision,
    target_hit_percentage,
    cep50,
    threshold,
    mode,
    impact_points,
    target_position,
    target_radius,
):
    ax.set_axis_off()
    ax.set_facecolor(_BG)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)

    # Left: decision banner + metrics
    left_ax = ax.inset_axes([0.02, 0.08, 0.36, 0.88])
    _draw_banner_and_metrics(
        left_ax,
        decision,
        target_hit_percentage,
        cep50,
        threshold,
        mode,
    )

    # Right: target / crosshair view
    right_ax = ax.inset_axes([0.42, 0.06, 0.56, 0.90])
    _draw_target_view(
        right_ax,
        impact_points,
        target_position,
        target_radius,
        cep50,
    )


def _draw_banner_and_metrics(ax, decision, target_hit_percentage, cep50, threshold, mode):
    ax.set_axis_off()
    ax.set_facecolor(_PANEL)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    for spine in ax.spines.values():
        spine.set_color(_BORDER)

    is_drop = decision.upper() == "DROP"
    color = _GREEN if is_drop else _RED
    label = "DROP" if is_drop else "NO DROP"

    # Decision banner (dominant)
    ax.axhspan(0.55, 0.88, xmin=0.06, xmax=0.94, facecolor=color, alpha=0.2)
    ax.text(0.5, 0.72, label, transform=ax.transAxes, fontsize=28, fontweight="bold",
            color=color, ha="center", va="center", family="monospace")

    # Key metrics (secondary)
    ax.text(0.5, 0.42, f"HIT   {target_hit_percentage:.1f}%", transform=ax.transAxes,
            fontsize=11, color=_TEXT, ha="center", va="center", family="monospace")
    ax.text(0.5, 0.30, f"CEP50 {cep50:.2f} m", transform=ax.transAxes,
            fontsize=10, color=_LABEL, ha="center", va="center", family="monospace")
    ax.text(0.5, 0.18, f"THR   {threshold:.1f}%", transform=ax.transAxes,
            fontsize=10, color=_LABEL, ha="center", va="center", family="monospace")
    ax.text(0.5, 0.06, mode or "—", transform=ax.transAxes,
            fontsize=9, color=_LABEL, ha="center", va="center", family="monospace")


def _draw_target_view(ax, impact_points, target_position, target_radius, cep50):
    impact_points = np.asarray(impact_points, dtype=float)
    target_position = np.asarray(target_position, dtype=float).reshape(2)

    ax.set_facecolor(_PANEL)
    ax.tick_params(colors=_LABEL)
    ax.xaxis.label.set_color(_LABEL)
    ax.yaxis.label.set_color(_LABEL)
    for spine in ax.spines.values():
        spine.set_color(_BORDER)
    ax.grid(True, color=_BORDER, alpha=0.4)

    if impact_points.size >= 2:
        ax.scatter(impact_points[:, 0], impact_points[:, 1], color=_SCATTER, alpha=0.35, s=8, edgecolors="none")
        mean_impact = np.mean(impact_points, axis=0)
        ax.scatter(mean_impact[0], mean_impact[1], color=_MEAN, s=60, zorder=5, marker="x", linewidths=2)

    ax.add_patch(plt.Circle(target_position, target_radius, color=_GREEN, fill=False, linewidth=1.5))
    ax.scatter(target_position[0], target_position[1], color=_GREEN, s=36, zorder=5, edgecolors=_PANEL, linewidths=0.5)

    if cep50 is not None and cep50 > 0:
        ax.add_patch(plt.Circle(target_position, cep50, color=_CEP, fill=False, linestyle="--", linewidth=1))

    _draw_crosshair(ax, target_position, 2.0)

    ax.set_xlabel("X (m)")
    ax.set_ylabel("Y (m)")
    ax.axis("equal")


def _draw_crosshair(ax, target_position, length_m):
    cx, cy = float(target_position[0]), float(target_position[1])
    ax.plot([cx - length_m, cx + length_m], [cy, cy], color=_GREEN, linewidth=1, alpha=0.8)
    ax.plot([cx, cx], [cy - length_m, cy + length_m], color=_GREEN, linewidth=1, alpha=0.8)
