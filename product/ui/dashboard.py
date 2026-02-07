"""
Product operator dashboard. Displays mission summary and advisory.
No physics, Monte Carlo, or policy logic. Deterministic for given inputs.
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches


def _fmt_payload(payload):
    """Format payload for display. No computation."""
    return (
        f"mass = {payload.mass:.2f} kg  |  "
        f"A = {payload.reference_area:.4f} m²  |  Cd = {payload.drag_coefficient:.2f}"
    )


def _fmt_target(target):
    """Format target for display."""
    x, y = target.position[0], target.position[1]
    return f"position = ({x:.1f}, {y:.1f}) m  |  radius = {target.radius:.1f} m"


def _fmt_environment(environment):
    """Format environment for display."""
    wx, wy, wz = environment.wind_mean[0], environment.wind_mean[1], environment.wind_mean[2]
    return f"wind mean = ({wx:.1f}, {wy:.1f}, {wz:.1f}) m/s  |  wind std = {environment.wind_std:.2f} m/s"


def build_dashboard_figure(
    mission_state,
    advisory_result,
    active_threshold_percent,
    active_mode,
):
    """
    Build a single figure with mission summary and advisory display.
    All inputs are precomputed; no engine or advisory calls.
    active_threshold_percent: float, 0–100.
    active_mode: str, e.g. "Conservative", "Balanced", "Aggressive".

    Returns (fig, ax_text) where ax_text is the main text axes.
    """
    fig, ax = plt.subplots(figsize=(10, 8))
    ax.set_axis_off()

    payload = mission_state.payload
    target = mission_state.target
    environment = mission_state.environment

    feasibility = advisory_result.current_feasibility
    hit_pct = advisory_result.current_P_hit * 100.0
    cep50 = advisory_result.current_cep50_m
    is_feasible = feasibility == "DROP"

    lines = [
        "——— Mission summary ———",
        "Payload: " + _fmt_payload(payload),
        "Target: " + _fmt_target(target),
        "Environment: " + _fmt_environment(environment),
        "",
        "——— Advisory ———",
        f"Decision: {feasibility}",
        f"Target Hit %: {hit_pct:.1f}%",
        f"CEP50: {cep50:.2f} m",
        f"Active threshold: {active_threshold_percent:.1f}%",
        f"Active mode: {active_mode}",
    ]

    text = "\n".join(lines)
    ax.text(0.05, 0.95, text, transform=ax.transAxes, fontsize=11,
            verticalalignment="top", fontfamily="monospace",
            bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.3))

    # Feasibility indicator
    color = "green" if is_feasible else "red"
    patch = mpatches.Patch(facecolor=color, alpha=0.4, label=feasibility)
    ax.legend(handles=[patch], loc="lower left", framealpha=0.9)
    ax.set_title("Operator dashboard — mission and advisory")

    return fig, ax


def build_dashboard_text(
    mission_state,
    advisory_result,
    active_threshold_percent,
    active_mode,
):
    """
    Return a single string with mission summary and advisory (for logging or CLI).
    No figure. Deterministic for given inputs.
    """
    payload = mission_state.payload
    target = mission_state.target
    environment = mission_state.environment
    feasibility = advisory_result.current_feasibility
    hit_pct = advisory_result.current_P_hit * 100.0
    cep50 = advisory_result.current_cep50_m

    lines = [
        "Mission summary",
        "  Payload: " + _fmt_payload(payload),
        "  Target: " + _fmt_target(target),
        "  Environment: " + _fmt_environment(environment),
        "Advisory",
        f"  Decision: {feasibility}",
        f"  Target Hit %: {hit_pct:.1f}%",
        f"  CEP50: {cep50:.2f} m",
        f"  Active threshold: {active_threshold_percent:.1f}%",
        f"  Active mode: {active_mode}",
    ]
    return "\n".join(lines)
