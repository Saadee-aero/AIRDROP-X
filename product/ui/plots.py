"""
Reusable plotting functions. No engine or advisory calls.
All inputs are precomputed data. SI units (m, m/s, etc.).
"""

import numpy as np
import matplotlib.pyplot as plt


def plot_impact_dispersion(
    ax,
    impact_points,
    target_position,
    target_radius,
    cep50=None,
):
    """
    Draw impact scatter, target circle, and optional CEP ring on ax.
    impact_points: (N, 2) array, m.
    target_position: (2,) or (x, y), m.
    target_radius: float, m.
    cep50: float or None, m. If set, draw circle of radius cep50 at target (confidence ring).
    """
    impact_points = np.asarray(impact_points, dtype=float)
    target_position = np.asarray(target_position, dtype=float).reshape(2)
    ax.scatter(impact_points[:, 0], impact_points[:, 1], alpha=0.4, s=8)
    ax.add_patch(
        plt.Circle(target_position, target_radius, color="r", fill=False)
    )
    ax.scatter(
        target_position[0], target_position[1], color="r", s=30, zorder=5
    )
    if cep50 is not None and cep50 > 0:
        ax.add_patch(
            plt.Circle(
                target_position, cep50, color="gray", fill=False, linestyle="--"
            )
        )
    ax.set_xlabel("X (m)")
    ax.set_ylabel("Y (m)")
    ax.axis("equal")
    ax.grid(True)


def plot_sensitivity(ax, x_values, y_values, x_label, y_label, title=None):
    """
    Line plot for sensitivity or replay. No engine calls.
    x_values, y_values: 1D arrays.
    """
    x_values = np.asarray(x_values, dtype=float)
    y_values = np.asarray(y_values, dtype=float)
    ax.plot(x_values, y_values)
    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    ax.grid(True)
    if title is not None:
        ax.set_title(title)


def create_figure_axes(nrows=1, ncols=1, figsize=(6, 6)):
    """Return (fig, ax or axs) for reuse. No state mutation."""
    fig, ax = plt.subplots(nrows, ncols, figsize=figsize)
    if nrows == 1 and ncols == 1:
        return fig, ax
    return fig, ax
