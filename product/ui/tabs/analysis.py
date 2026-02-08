"""
Analysis tab. Read-only display of analysis and sensitivity plots.
No sliders, no inputs, no recomputation. For understanding only.
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

from product.ui import plots

_BG = "#0a0c0a"
_PANEL = "#0f120f"
_LABEL = "#6b8e6b"
_TEXT = "#c0d0c0"
_BORDER = "#2a3a2a"
_PLACEHOLDER = "#4a5a4a"


def _placeholder_panel(ax, title, message="No sweep data available"):
    """Subdued placeholder when precomputed curve is not provided."""
    ax.set_axis_off()
    ax.set_facecolor(_PANEL)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.add_patch(mpatches.Rectangle((0.02, 0.02), 0.96, 0.96, linewidth=1,
                edgecolor=_BORDER, facecolor="none", transform=ax.transAxes))
    ax.text(0.5, 0.6, title, transform=ax.transAxes, fontsize=10,
            color=_LABEL, ha="center", va="center", family="monospace")
    ax.text(0.5, 0.4, message, transform=ax.transAxes, fontsize=8,
            color=_PLACEHOLDER, ha="center", va="center", family="monospace")


def _cep_summary_panel(ax, cep50, target_hit_percentage):
    """Read-only CEP and hit probability summary."""
    ax.set_axis_off()
    ax.set_facecolor(_PANEL)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.add_patch(mpatches.Rectangle((0.02, 0.02), 0.96, 0.96, linewidth=1,
                edgecolor=_BORDER, facecolor="none", transform=ax.transAxes))
    ax.text(0.5, 0.88, "CEP SUMMARY", transform=ax.transAxes, fontsize=10,
            color=_LABEL, ha="center", va="top", family="monospace")
    y = 0.68
    dy = 0.14
    if cep50 is not None:
        ax.text(0.1, y, "CEP50", transform=ax.transAxes, fontsize=9, color=_LABEL, va="center", family="monospace")
        ax.text(0.9, y, f"{float(cep50):.2f} m", transform=ax.transAxes, fontsize=9, color=_TEXT, ha="right", va="center", family="monospace")
        y -= dy
    if target_hit_percentage is not None:
        ax.text(0.1, y, "Hit %", transform=ax.transAxes, fontsize=9, color=_LABEL, va="center", family="monospace")
        ax.text(0.9, y, f"{float(target_hit_percentage):.1f}%", transform=ax.transAxes, fontsize=9, color=_TEXT, ha="right", va="center", family="monospace")
        y -= dy
    ax.text(0.5, 0.22, "Read-only · No recomputation", transform=ax.transAxes, fontsize=7,
            color=_PLACEHOLDER, ha="center", va="center", family="monospace")


def render(
    ax,
    impact_points=None,
    target_position=None,
    target_radius=None,
    cep50=None,
    target_hit_percentage=None,
    prob_vs_distance=None,
    prob_vs_wind_uncertainty=None,
    **_
):
    """
    Draw Analysis tab. All arguments optional. Read-only; no recomputation.
    - prob_vs_distance: (x_values, y_values) for P_hit vs target distance
    - prob_vs_wind_uncertainty: (x_values, y_values) for P_hit vs wind uncertainty
    """
    ax.set_axis_off()
    ax.set_facecolor(_BG)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)

    # 2x2 layout: top-left prob vs distance, top-right impact dispersion,
    # bottom-left prob vs wind uncertainty, bottom-right CEP summary
    margin = 0.02
    w = 0.46
    h = 0.44
    gap = 0.02
    tl = [margin, 0.5 + gap, w, h]
    tr = [margin + w + gap, 0.5 + gap, w, h]
    bl = [margin, margin, w, h]
    br = [margin + w + gap, margin, w, h]

    # Top-left: Probability vs target distance
    ax_tl = ax.inset_axes(tl)
    if prob_vs_distance is not None and len(prob_vs_distance) == 2:
        x_vals, y_vals = prob_vs_distance[0], prob_vs_distance[1]
        if len(x_vals) and len(y_vals):
            plots.plot_sensitivity(
                ax_tl, x_vals, y_vals,
                "Target distance (m)", "Hit probability",
                title="P hit vs target distance",
            )
        else:
            _placeholder_panel(ax_tl, "P hit vs target distance")
    else:
        _placeholder_panel(ax_tl, "P hit vs target distance")

    # Top-right: Impact dispersion
    ax_tr = ax.inset_axes(tr)
    if impact_points is not None and target_position is not None and np.size(impact_points) >= 2:
        impact_points = np.asarray(impact_points, dtype=float)
        if impact_points.ndim == 1:
            impact_points = impact_points.reshape(-1, 2)
        plots.plot_impact_dispersion(
            ax_tr, impact_points, target_position, target_radius or 0, cep50
        )
        ax_tr.set_title("Impact dispersion", color=_LABEL, fontsize=9, family="monospace")
    else:
        _placeholder_panel(ax_tr, "Impact dispersion", "No impact data")

    # Bottom-left: Probability vs wind uncertainty
    ax_bl = ax.inset_axes(bl)
    if prob_vs_wind_uncertainty is not None and len(prob_vs_wind_uncertainty) == 2:
        x_vals, y_vals = prob_vs_wind_uncertainty[0], prob_vs_wind_uncertainty[1]
        if len(x_vals) and len(y_vals):
            plots.plot_sensitivity(
                ax_bl, x_vals, y_vals,
                "Wind uncertainty (m/s)", "Hit probability",
                title="P hit vs wind uncertainty",
            )
        else:
            _placeholder_panel(ax_bl, "P hit vs wind uncertainty")
    else:
        _placeholder_panel(ax_bl, "P hit vs wind uncertainty")

    # Bottom-right: CEP summary
    ax_br = ax.inset_axes(br)
    _cep_summary_panel(ax_br, cep50, target_hit_percentage)
