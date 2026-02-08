"""
Target reticle view: military HUD style. Dark panel, green reticle.
"""

import numpy as np

from . import plots

CROSSHAIR_LENGTH_M = 2.0

_RETICLE = "#00ff41"
_PANEL = "#0f120f"
_LABEL = "#6b8e6b"
_BORDER = "#2a3a2a"


def _draw_crosshair(ax, target_position, length_m):
    cx, cy = float(target_position[0]), float(target_position[1])
    ax.plot([cx - length_m, cx + length_m], [cy, cy], color=_RETICLE, linewidth=1, alpha=0.9)
    ax.plot([cx, cx], [cy - length_m, cy + length_m], color=_RETICLE, linewidth=1, alpha=0.9)


def draw_crosshair(
    ax,
    impact_points,
    target_position,
    target_radius,
    cep50,
    crosshair_length_m=None,
):
    length_m = crosshair_length_m if crosshair_length_m is not None else CROSSHAIR_LENGTH_M
    plots.plot_impact_dispersion(
        ax, impact_points, target_position, target_radius, cep50=cep50
    )
    _draw_crosshair(ax, target_position, length_m)
    ax.set_title("TARGET VIEW", color=_LABEL, fontsize=10, family="monospace")
