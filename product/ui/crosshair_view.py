"""
Target reticle view with impact dispersion and CEP ring.
Clearly indicates feasible vs non-feasible. Equal axis. No computation.
"""

import numpy as np
import matplotlib.pyplot as plt

from . import plots

# Crosshair half-length in axes-relative units; scale by data for visibility
CROSSHAIR_LENGTH_M = 2.0


def _draw_crosshair(ax, target_position, length_m):
    """Draw crosshair at target center. length_m: half-length of each arm (m)."""
    cx, cy = float(target_position[0]), float(target_position[1])
    ax.plot([cx - length_m, cx + length_m], [cy, cy], color="k", linewidth=1)
    ax.plot([cx, cx], [cy - length_m, cy + length_m], color="k", linewidth=1)


def crosshair_view(
    impact_points,
    target_position,
    target_radius,
    cep50,
    feasible,
    ax=None,
    crosshair_length_m=None,
):
    """
    Draw target reticle, impact dispersion, CEP confidence ring, and feasibility.
    All inputs precomputed. No engine or advisory calls.
    feasible: bool or str "DROP" / "NO DROP". True or "DROP" = feasible.

    Returns the axes used.
    """
    impact_points = np.asarray(impact_points, dtype=float)
    target_position = np.asarray(target_position, dtype=float).reshape(2)
    if ax is None:
        fig, ax = plt.subplots(figsize=(8, 8))
    length_m = crosshair_length_m if crosshair_length_m is not None else CROSSHAIR_LENGTH_M

    plots.plot_impact_dispersion(
        ax, impact_points, target_position, target_radius, cep50=cep50
    )
    _draw_crosshair(ax, target_position, length_m)

    is_feasible = feasible is True or feasible == "DROP"
    status_text = "Feasible (DROP)" if is_feasible else "Not feasible (NO DROP)"
    status_color = "green" if is_feasible else "red"
    ax.set_title(f"Target view — {status_text}", color=status_color)

    return ax


def figure_crosshair_view(
    impact_points,
    target_position,
    target_radius,
    cep50,
    feasible,
    crosshair_length_m=None,
):
    """
    Create a new figure with crosshair view. Returns (fig, ax).
    """
    fig, ax = plt.subplots(figsize=(8, 8))
    crosshair_view(
        impact_points,
        target_position,
        target_radius,
        cep50,
        feasible,
        ax=ax,
        crosshair_length_m=crosshair_length_m,
    )
    return fig, ax
