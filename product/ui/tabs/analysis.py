"""
Analysis tab. Read-only display of analysis and sensitivity plots.
No sliders, no inputs, no recomputation. For understanding only.
"""

import numpy as np
import matplotlib.patches as mpatches

from product.ui import plots

# Import unified military-grade theme
from product.ui.ui_theme import (
    BG_MAIN,
    BG_PANEL,
    TEXT_PRIMARY,
    TEXT_LABEL,
    BORDER_SUBTLE,
)


def _placeholder_panel(
    ax,
    title,
    message="Sensitivity sweep not performed.\nUse Opportunity Analysis to generate sweep.",
):
    """Subdued placeholder when precomputed curve is not provided."""
    ax.set_axis_off()
    ax.set_facecolor(BG_PANEL)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.add_patch(
        mpatches.Rectangle(
            (0.02, 0.02),
            0.96,
            0.96,
            linewidth=1,
            edgecolor=BORDER_SUBTLE,
            facecolor="none",
            transform=ax.transAxes,
        )
    )
    ax.text(
        0.5,
        0.6,
        title,
        transform=ax.transAxes,
        fontsize=10,
        color=TEXT_LABEL,
        ha="center",
        va="center",
        family="monospace",
    )
    ax.text(
        0.5,
        0.4,
        message,
        transform=ax.transAxes,
        fontsize=8,
        color=TEXT_LABEL,
        ha="center",
        va="center",
        family="monospace",
    )


def _impact_dynamics_panel(
    ax, impact_velocity_stats, max_safe_impact_speed=None
):
    """IMPACT DYNAMICS panel: mean, std, p95 impact speed + advanced note."""
    ax.set_axis_off()
    ax.set_facecolor(BG_PANEL)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.add_patch(
        mpatches.Rectangle(
            (0.02, 0.02),
            0.96,
            0.96,
            linewidth=1,
            edgecolor=BORDER_SUBTLE,
            facecolor="none",
            transform=ax.transAxes,
        )
    )
    ax.text(
        0.5,
        0.92,
        "IMPACT DYNAMICS",
        transform=ax.transAxes,
        fontsize=10,
        color=TEXT_LABEL,
        ha="center",
        va="top",
        family="monospace",
    )
    y = 0.70
    dy = 0.22
    if impact_velocity_stats:
        ax.text(
            0.1,
            y,
            "Mean impact speed",
            transform=ax.transAxes,
            fontsize=9,
            color=TEXT_LABEL,
            va="center",
            ha="left",
            family="monospace",
        )
        ax.text(
            0.9,
            y,
            f"{impact_velocity_stats.get('mean_impact_speed', 0):.2f} m/s",
            transform=ax.transAxes,
            fontsize=9,
            color=TEXT_PRIMARY,
            ha="right",
            va="center",
            family="monospace",
        )
        y -= dy
        ax.text(
            0.1,
            y,
            "Std dev",
            transform=ax.transAxes,
            fontsize=9,
            color=TEXT_LABEL,
            va="center",
            ha="left",
            family="monospace",
        )
        ax.text(
            0.9,
            y,
            f"{impact_velocity_stats.get('std_impact_speed', 0):.2f} m/s",
            transform=ax.transAxes,
            fontsize=9,
            color=TEXT_PRIMARY,
            ha="right",
            va="center",
            family="monospace",
        )
        y -= dy
        ax.text(
            0.1,
            y,
            "95% percentile",
            transform=ax.transAxes,
            fontsize=9,
            color=TEXT_LABEL,
            va="center",
            ha="left",
            family="monospace",
        )
        ax.text(
            0.9,
            y,
            f"{impact_velocity_stats.get('p95_impact_speed', 0):.2f} m/s",
            transform=ax.transAxes,
            fontsize=9,
            color=TEXT_PRIMARY,
            ha="right",
            va="center",
            family="monospace",
        )
        y -= dy
    if max_safe_impact_speed is not None and impact_velocity_stats:
        p95 = float(impact_velocity_stats.get("p95_impact_speed", 0.0))
        safe = float(max_safe_impact_speed)
        ratio = p95 / max(safe, 1e-9)
        if ratio <= 0.80:
            risk = "LOW"
        elif ratio <= 1.00:
            risk = "MODERATE"
        else:
            risk = "HIGH"
        ax.text(
            0.1,
            y,
            "Survivability Risk",
            transform=ax.transAxes,
            fontsize=9,
            color=TEXT_LABEL,
            va="center",
            ha="left",
            family="monospace",
        )
        ax.text(
            0.9,
            y,
            risk,
            transform=ax.transAxes,
            fontsize=9,
            color=TEXT_PRIMARY,
            ha="right",
            va="center",
            family="monospace",
        )
        y -= dy
    else:
        ax.text(
            0.5,
            max(y, 0.24),
            "No structural limit defined.",
            transform=ax.transAxes,
            fontsize=8,
            color=TEXT_LABEL,
            ha="center",
            va="center",
            family="monospace",
        )
    ax.text(
        0.5,
        0.12,
        "Impact survivability depends on payload structural limits.",
        transform=ax.transAxes,
        fontsize=7,
        color=TEXT_LABEL,
        ha="center",
        va="center",
        family="monospace",
        wrap=True,
    )


def _cep_summary_panel(ax, cep50, target_hit_percentage):
    """Read-only CEP and hit probability summary."""
    ax.set_axis_off()
    ax.set_facecolor(BG_PANEL)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.add_patch(
        mpatches.Rectangle(
            (0.02, 0.02),
            0.96,
            0.96,
            linewidth=1,
            edgecolor=BORDER_SUBTLE,
            facecolor="none",
            transform=ax.transAxes,
        )
    )
    ax.text(
        0.5,
        0.92,
        "CEP SUMMARY",
        transform=ax.transAxes,
        fontsize=10,
        color=TEXT_LABEL,
        ha="center",
        va="top",
        family="monospace",
        weight="bold",
    )
    y = 0.70
    dy = 0.16
    if cep50 is not None:
        ax.text(
            0.1,
            y,
            "CEP50",
            transform=ax.transAxes,
            fontsize=9,
            color=TEXT_LABEL,
            va="center",
            ha="left",
            family="monospace",
        )
        ax.text(
            0.9,
            y,
            f"{float(cep50):.2f} m",
            transform=ax.transAxes,
            fontsize=9,
            color=TEXT_PRIMARY,
            ha="right",
            va="center",
            family="monospace",
        )
        y -= dy
    if target_hit_percentage is not None:
        ax.text(
            0.1,
            y,
            "Hit %",
            transform=ax.transAxes,
            fontsize=9,
            color=TEXT_LABEL,
            va="center",
            ha="left",
            family="monospace",
        )
        ax.text(
            0.9,
            y,
            f"{float(target_hit_percentage):.1f}%",
            transform=ax.transAxes,
            fontsize=9,
            color=TEXT_PRIMARY,
            ha="right",
            va="center",
            family="monospace",
        )
        y -= dy
    ax.text(
        0.5,
        0.22,
        "Read-only · No recomputation",
        transform=ax.transAxes,
        fontsize=7,
        color=TEXT_LABEL,
        ha="center",
        va="center",
        family="monospace",
    )


def _topology_panel(ax, topology_matrix):
    """AX-MISS-TOPOLOGY-HYBRID-12: Full topology for advanced fidelity."""
    ax.set_axis_off()
    ax.set_facecolor(BG_PANEL)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.add_patch(
        mpatches.Rectangle(
            (0.02, 0.02),
            0.96,
            0.96,
            linewidth=1,
            edgecolor=BORDER_SUBTLE,
            facecolor="none",
            transform=ax.transAxes,
        )
    )
    ax.text(
        0.5,
        0.92,
        "TOPOLOGY",
        transform=ax.transAxes,
        fontsize=10,
        color=TEXT_LABEL,
        ha="center",
        va="top",
        family="monospace",
        weight="bold",
    )
    if not topology_matrix or not isinstance(topology_matrix, dict):
        ax.text(
            0.5,
            0.5,
            "No topology data",
            transform=ax.transAxes,
            fontsize=9,
            color=TEXT_LABEL,
            ha="center",
            va="center",
            family="monospace",
        )
        return
    y = 0.68
    dy = 0.20
    ecc = topology_matrix.get("eccentricity_ratio")
    ang = topology_matrix.get("principal_axis_angle_deg")
    cls = topology_matrix.get("dispersion_classification", "—")
    if ecc is not None:
        ax.text(0.1, y, "Eccentricity", transform=ax.transAxes, fontsize=9, color=TEXT_LABEL, va="center", ha="left", family="monospace")
        ax.text(0.9, y, f"{float(ecc):.3f}", transform=ax.transAxes, fontsize=9, color=TEXT_PRIMARY, ha="right", va="center", family="monospace")
        y -= dy
    if ang is not None:
        ax.text(0.1, y, "Principal axis (°)", transform=ax.transAxes, fontsize=9, color=TEXT_LABEL, va="center", ha="left", family="monospace")
        ax.text(0.9, y, f"{float(ang):.1f}", transform=ax.transAxes, fontsize=9, color=TEXT_PRIMARY, ha="right", va="center", family="monospace")
        y -= dy
    ax.text(0.1, y, "Classification", transform=ax.transAxes, fontsize=9, color=TEXT_LABEL, va="center", ha="left", family="monospace")
    ax.text(0.9, y, str(cls), transform=ax.transAxes, fontsize=9, color=TEXT_PRIMARY, ha="right", va="center", family="monospace")


def _release_corridor_panel(ax, release_corridor_matrix):
    """AX-RELEASE-CORRIDOR-19: Release corridor span for advanced fidelity."""
    ax.set_axis_off()
    ax.set_facecolor(BG_PANEL)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.add_patch(
        mpatches.Rectangle(
            (0.02, 0.02), 0.96, 0.96,
            linewidth=1, edgecolor=BORDER_SUBTLE, facecolor="none", transform=ax.transAxes,
        )
    )
    ax.text(0.5, 0.92, "RELEASE CORRIDOR", transform=ax.transAxes, fontsize=10, color=TEXT_LABEL,
            ha="center", va="top", family="monospace", weight="bold")
    if not release_corridor_matrix or not isinstance(release_corridor_matrix, dict):
        ax.text(0.5, 0.5, "No corridor data", transform=ax.transAxes, fontsize=9,
                color=TEXT_LABEL, ha="center", va="center", family="monospace")
        return
    w = release_corridor_matrix.get("corridor_width_m")
    mn = release_corridor_matrix.get("min_offset_m")
    mx = release_corridor_matrix.get("max_offset_m")
    y = 0.55
    if w is not None:
        ax.text(0.1, y, "Width", transform=ax.transAxes, fontsize=9, color=TEXT_LABEL, va="center", ha="left", family="monospace")
        w_str = f"{w} m" if isinstance(w, str) else f"{float(w):.1f} m"
        ax.text(0.9, y, w_str, transform=ax.transAxes, fontsize=9, color=TEXT_PRIMARY, ha="right", va="center", family="monospace")
        y -= 0.25
    if mn is not None and mx is not None:
        ax.text(0.1, y, "Span", transform=ax.transAxes, fontsize=9, color=TEXT_LABEL, va="center", ha="left", family="monospace")
        ax.text(0.9, y, f"{float(mn):.0f} to +{float(mx):.0f} m", transform=ax.transAxes, fontsize=9, color=TEXT_PRIMARY, ha="right", va="center", family="monospace")


def _fragility_panel(ax, fragility_state):
    """AX-FRAGILITY-SURFACE-20: Fragility zone for advanced fidelity."""
    ax.set_axis_off()
    ax.set_facecolor(BG_PANEL)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.add_patch(
        mpatches.Rectangle(
            (0.02, 0.02), 0.96, 0.96,
            linewidth=1, edgecolor=BORDER_SUBTLE, facecolor="none", transform=ax.transAxes,
        )
    )
    ax.text(0.5, 0.92, "FRAGILITY", transform=ax.transAxes, fontsize=10, color=TEXT_LABEL,
            ha="center", va="top", family="monospace", weight="bold")
    if not fragility_state or not isinstance(fragility_state, dict):
        ax.text(0.5, 0.5, "No fragility data", transform=ax.transAxes, fontsize=9,
                color=TEXT_LABEL, ha="center", va="center", family="monospace")
        return
    zone = fragility_state.get("zone", "—")
    margin = fragility_state.get("margin_pct")
    y = 0.55
    ax.text(0.1, y, "Zone", transform=ax.transAxes, fontsize=9, color=TEXT_LABEL, va="center", ha="left", family="monospace")
    ax.text(0.9, y, str(zone), transform=ax.transAxes, fontsize=9, color=TEXT_PRIMARY, ha="right", va="center", family="monospace")
    y -= 0.22
    if margin is not None:
        ax.text(0.1, y, "Margin", transform=ax.transAxes, fontsize=9, color=TEXT_LABEL, va="center", ha="left", family="monospace")
        ax.text(0.9, y, f"{float(margin):+.1f}%", transform=ax.transAxes, fontsize=9, color=TEXT_PRIMARY, ha="right", va="center", family="monospace")


def _uncertainty_panel(ax, uncertainty_contribution):
    """AX-UNCERTAINTY-DECOMPOSITION-21: Contribution weights for advanced fidelity."""
    ax.set_axis_off()
    ax.set_facecolor(BG_PANEL)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.add_patch(
        mpatches.Rectangle(
            (0.02, 0.02), 0.96, 0.96,
            linewidth=1, edgecolor=BORDER_SUBTLE, facecolor="none", transform=ax.transAxes,
        )
    )
    ax.text(0.5, 0.95, "UNCERTAINTY CONTRIBUTION", transform=ax.transAxes, fontsize=9, color=TEXT_LABEL,
            ha="center", va="top", family="monospace", weight="bold")
    if not uncertainty_contribution or not isinstance(uncertainty_contribution, dict):
        ax.text(0.5, 0.5, "No contribution data", transform=ax.transAxes, fontsize=8,
                color=TEXT_LABEL, ha="center", va="center", family="monospace")
        return
    items = [
        ("wind", "Wind", 0.62),
        ("altitude", "Altitude", 0.38),
        ("velocity", "Velocity", 0.14),
    ]
    for key, label, y_pos in items:
        pct = float(uncertainty_contribution.get(key, 0) or 0) * 100.0
        ax.text(0.08, y_pos, label, transform=ax.transAxes, fontsize=8, color=TEXT_LABEL, va="center", ha="left", family="monospace")
        ax.add_patch(
            mpatches.Rectangle(
                (0.22, y_pos - 0.03), max(0.02, pct / 100.0 * 0.68), 0.06,
                facecolor=TEXT_PRIMARY, alpha=0.6, transform=ax.transAxes,
            )
        )
        ax.text(0.92, y_pos, f"{pct:.0f}%", transform=ax.transAxes, fontsize=8, color=TEXT_PRIMARY, ha="right", va="center", family="monospace")


def _sensitivity_matrix_panel(ax, sensitivity_matrix, dominant_risk_factor=None):
    """AX-SENSITIVITY-HYBRID-09: Full sensitivity table for advanced fidelity."""
    ax.set_axis_off()
    ax.set_facecolor(BG_PANEL)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.add_patch(
        mpatches.Rectangle(
            (0.02, 0.02),
            0.96,
            0.96,
            linewidth=1,
            edgecolor=BORDER_SUBTLE,
            facecolor="none",
            transform=ax.transAxes,
        )
    )
    ax.text(
        0.5,
        0.92,
        "SENSITIVITY MATRIX",
        transform=ax.transAxes,
        fontsize=10,
        color=TEXT_LABEL,
        ha="center",
        va="top",
        family="monospace",
        weight="bold",
    )
    if not sensitivity_matrix or not isinstance(sensitivity_matrix, dict):
        ax.text(
            0.5,
            0.5,
            "No sensitivity data",
            transform=ax.transAxes,
            fontsize=9,
            color=TEXT_LABEL,
            ha="center",
            va="center",
            family="monospace",
        )
        return
    y = 0.72
    dy = 0.18
    for key, label in [("wind", "Wind (∂P/∂W)"), ("altitude", "Altitude (∂P/∂H)"), ("velocity", "Velocity (∂P/∂V)")]:
        val = sensitivity_matrix.get(key, 0)
        dom = " ← dominant" if dominant_risk_factor == key else ""
        ax.text(
            0.1,
            y,
            label,
            transform=ax.transAxes,
            fontsize=9,
            color=TEXT_LABEL,
            va="center",
            ha="left",
            family="monospace",
        )
        ax.text(
            0.9,
            y,
            f"{float(val):.4f}{dom}",
            transform=ax.transAxes,
            fontsize=9,
            color=TEXT_PRIMARY,
            ha="right",
            va="center",
            family="monospace",
        )
        y -= dy


def render(
    ax,
    impact_points=None,
    target_position=None,
    target_radius=None,
    uav_position=None,
    wind_mean=None,
    cep50=None,
    target_hit_percentage=None,
    prob_vs_distance=None,
    prob_vs_wind_uncertainty=None,
    impact_velocity_stats=None,
    max_safe_impact_speed=None,
    sensitivity_matrix=None,
    dominant_risk_factor=None,
    topology_matrix=None,
    release_corridor_matrix=None,
    fragility_state=None,
    uncertainty_contribution=None,
    dispersion_mode="standard",
    view_zoom=1.0,
    snapshot_timestamp=None,
    random_seed=None,
    n_samples=None,
    **_,
):
    """
    Draw Analysis tab. All arguments optional. Read-only; no recomputation.
    - prob_vs_distance: (x_values, y_values) for P_hit vs target distance
    - prob_vs_wind_uncertainty: (x_values, y_values) for P_hit vs wind uncertainty
    """
    ax.set_axis_off()
    ax.set_facecolor(BG_MAIN)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)

    # 2x2 + bottom row (wind, CEP, sensitivity/impact, topology, corridor, fragility, uncertainty)
    margin = 0.02
    w_top = 0.46
    w_bot = 0.12
    h_bottom = 0.40
    h_top = 0.38
    gap = 0.01
    tl = [margin, 1.0 - margin - h_top, w_top, h_top]
    tr = [margin + w_top + gap, 1.0 - margin - h_top, w_top, h_top]
    bl = [margin, margin, w_bot, h_bottom]
    bm = [margin + w_bot + gap, margin, w_bot, h_bottom]
    br = [margin + 2 * (w_bot + gap), margin, w_bot, h_bottom]
    bt = [margin + 3 * (w_bot + gap), margin, w_bot, h_bottom]
    b5 = [margin + 4 * (w_bot + gap), margin, w_bot, h_bottom]
    b6 = [margin + 5 * (w_bot + gap), margin, w_bot, h_bottom]
    b7 = [margin + 6 * (w_bot + gap), margin, w_bot, h_bottom]

    # Top-left: Probability vs target distance
    ax_tl = ax.inset_axes(tl)
    ax_tl.set_clip_on(True)
    if prob_vs_distance is not None and len(prob_vs_distance) == 2:
        x_vals, y_vals = prob_vs_distance[0], prob_vs_distance[1]
        if len(x_vals) and len(y_vals):
            plots.plot_sensitivity(
                ax_tl,
                x_vals,
                y_vals,
                "Target distance (m)",
                "Hit probability",
                title="P(HIT) vs TARGET DISTANCE",
            )
        else:
            _placeholder_panel(ax_tl, "P(HIT) vs TARGET DISTANCE")
    else:
        _placeholder_panel(ax_tl, "P(HIT) vs TARGET DISTANCE")

    # Top-right: Impact dispersion
    ax_tr = ax.inset_axes(tr)
    ax_tr.set_clip_on(True)
    if (
        impact_points is not None
        and target_position is not None
        and np.size(impact_points) >= 2
    ):
        print("ANALYSIS DISPLAY MODE:", dispersion_mode)
        print("IMPACT COUNT:", np.size(impact_points) // 2 if impact_points is not None else 0)
        impact_points = np.asarray(impact_points, dtype=float)
        if impact_points.ndim == 1:
            impact_points = impact_points.reshape(-1, 2)
        wind_speed = float(np.linalg.norm(wind_mean[:2])) if wind_mean is not None and np.size(wind_mean) >= 2 else 0.0
        p_hit_for_color = None
        if target_hit_percentage is not None:
            try:
                p_hit_val = float(target_hit_percentage)
                p_hit_for_color = p_hit_val / 100.0 if p_hit_val > 1.0 else p_hit_val
            except Exception:
                p_hit_for_color = None
        mode_val = str(dispersion_mode).strip().lower()
        if mode_val not in ("standard", "advanced"):
            mode_val = "standard"
        plots.plot_impact_dispersion(
            ax_tr,
            impact_points,
            target_position,
            target_radius or 0,
            cep50,
            release_point=(
                uav_position[:2] if uav_position is not None else None
            ),
            wind_vector=(wind_mean[:2] if wind_mean is not None else None),
            mode=mode_val,
            P_hit=p_hit_for_color,
            wind_speed=wind_speed,
            show_density=(mode_val == "advanced"),
            view_zoom=view_zoom,
        )
        mode_badge = "STANDARD DISPLAY" if mode_val == "standard" else "ADVANCED DISPLAY"
        dot_color = "#00FF66" if mode_val == "standard" else "#ffaa00"
        ax_tr.add_patch(
            mpatches.Circle(
                (0.02, 0.98),
                0.008,
                transform=ax_tr.transAxes,
                facecolor=dot_color,
                edgecolor="none",
                zorder=10,
            )
        )
        ax_tr.text(
            0.042,
            0.98,
            f"IMPACT DISPERSION — {mode_badge}",
            transform=ax_tr.transAxes,
            va="top",
            ha="left",
            fontsize=9,
            color=TEXT_LABEL,
            family="monospace",
            weight="bold",
            zorder=10,
        )
    else:
        _placeholder_panel(ax_tr, "IMPACT DISPERSION", "No impact data")

    # Bottom-left: Probability vs wind uncertainty
    ax_bl = ax.inset_axes(bl)
    ax_bl.set_clip_on(True)
    if (
        prob_vs_wind_uncertainty is not None
        and len(prob_vs_wind_uncertainty) == 2
    ):
        x_vals, y_vals = (
            prob_vs_wind_uncertainty[0],
            prob_vs_wind_uncertainty[1],
        )
        if len(x_vals) and len(y_vals):
            plots.plot_sensitivity(
                ax_bl,
                x_vals,
                y_vals,
                "Wind uncertainty (m/s)",
                "Hit probability",
                title="P(HIT) vs WIND UNCERTAINTY",
            )
        else:
            _placeholder_panel(ax_bl, "P(HIT) vs WIND UNCERTAINTY")
    else:
        _placeholder_panel(ax_bl, "P(HIT) vs WIND UNCERTAINTY")

    # Bottom-center: CEP summary
    ax_bm = ax.inset_axes(bm)
    ax_bm.set_clip_on(True)
    _cep_summary_panel(ax_bm, cep50, target_hit_percentage)

    # Bottom-right: SENSITIVITY MATRIX (if ANALYTICAL) or IMPACT DYNAMICS
    ax_br = ax.inset_axes(br)
    ax_br.set_clip_on(True)
    if sensitivity_matrix is not None:
        _sensitivity_matrix_panel(
            ax_br,
            sensitivity_matrix,
            dominant_risk_factor=dominant_risk_factor,
        )
    else:
        _impact_dynamics_panel(
            ax_br,
            impact_velocity_stats,
            max_safe_impact_speed=max_safe_impact_speed,
        )

    # Bottom-right+1: TOPOLOGY (if ANALYTICAL)
    ax_bt = ax.inset_axes(bt)
    ax_bt.set_clip_on(True)
    if topology_matrix is not None:
        _topology_panel(ax_bt, topology_matrix)
    else:
        _placeholder_panel(ax_bt, "TOPOLOGY", "No topology data")

    # AX-RELEASE-CORRIDOR-19: Release corridor panel
    ax_b5 = ax.inset_axes(b5)
    ax_b5.set_clip_on(True)
    if release_corridor_matrix is not None:
        _release_corridor_panel(ax_b5, release_corridor_matrix)
    else:
        _placeholder_panel(ax_b5, "RELEASE CORRIDOR", "No corridor data")

    # AX-FRAGILITY-SURFACE-20: Fragility panel
    ax_b6 = ax.inset_axes(b6)
    ax_b6.set_clip_on(True)
    if fragility_state is not None:
        _fragility_panel(ax_b6, fragility_state)
    else:
        _placeholder_panel(ax_b6, "FRAGILITY", "No fragility data")

    # AX-UNCERTAINTY-DECOMPOSITION-21: Uncertainty contribution panel
    ax_b7 = ax.inset_axes(b7)
    ax_b7.set_clip_on(True)
    if uncertainty_contribution is not None:
        _uncertainty_panel(ax_b7, uncertainty_contribution)
    else:
        _placeholder_panel(ax_b7, "UNCERTAINTY", "No contribution data")

    if snapshot_timestamp is not None:
        ax.text(
            0.5,
            0.01,
            f"Snapshot: {snapshot_timestamp or '---'} | Seed: {random_seed if random_seed is not None else '---'} | Samples: {n_samples if n_samples is not None else '---'}",
            transform=ax.transAxes,
            ha="center",
            va="bottom",
            color=TEXT_LABEL,
            fontsize=7,
            family="monospace",
        )
