"""
Decision Banner: fire-control advisory style. Military HUD look.
No plotting, no logic, no engine calls.
"""

from matplotlib.patches import Rectangle

_BG = "#0a0c0a"
_PANEL = "#0f120f"
_GREEN = "#00ff41"
_RED = "#ff3333"
_AMBER = "#ffb000"
_LABEL = "#6b8e6b"
_TEXT = "#c0d0c0"
_BORDER = "#2a3a2a"


def _fmt_payload(payload):
    return (
        f"mass = {payload.mass:.2f} kg  |  "
        f"A = {payload.reference_area:.4f} m²  |  Cd = {payload.drag_coefficient:.2f}"
    )


def _fmt_target(target):
    x, y = target.position[0], target.position[1]
    return f"position = ({x:.1f}, {y:.1f}) m  |  radius = {target.radius:.1f} m"


def _fmt_environment(environment):
    wx, wy, wz = environment.wind_mean[0], environment.wind_mean[1], environment.wind_mean[2]
    return f"wind mean = ({wx:.1f}, {wy:.1f}, {wz:.1f}) m/s  |  wind std = {environment.wind_std:.2f} m/s"


def draw_dashboard(
    ax,
    mission_state,
    advisory_result,
    threshold_percent,
    mode,
    decision_override=None,
    threshold_override=None,
    mode_override=None,
):
    ax.set_axis_off()
    ax.set_facecolor(_PANEL)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)

    decision = decision_override if decision_override is not None else advisory_result.current_feasibility
    hit_pct = advisory_result.current_P_hit * 100.0
    cep50 = advisory_result.current_cep50_m
    thresh = threshold_override if threshold_override is not None else threshold_percent
    mode_str = mode_override if mode_override is not None else mode

    is_feasible = decision == "DROP"
    decision_color = _GREEN if is_feasible else _RED

    # Panel border
    rect = Rectangle((0.005, 0.005), 0.99, 0.99, linewidth=1, edgecolor=_BORDER,
                     facecolor="none", transform=ax.transAxes)
    ax.add_patch(rect)

    # Header
    ax.text(0.5, 0.92, "ADVISORY", transform=ax.transAxes, fontsize=9,
            color=_LABEL, ha="center", va="center", family="monospace")

    # Decision strip
    ax.axhspan(0.48, 0.72, xmin=0.04, xmax=0.96, facecolor=decision_color, alpha=0.15, transform=ax.transAxes)
    ax.axhline(0.48, xmin=0.04, xmax=0.96, color=_BORDER, linewidth=0.8)
    ax.axhline(0.72, xmin=0.04, xmax=0.96, color=_BORDER, linewidth=0.8)
    ax.text(0.5, 0.60, decision, transform=ax.transAxes, fontsize=28, fontweight="bold",
            color=decision_color, ha="center", va="center", family="monospace")

    # Stats line
    ax.text(0.5, 0.32, f"HIT {hit_pct:.1f}%  |  THRESH {thresh:.1f}%",
            transform=ax.transAxes, fontsize=10, color=_TEXT, ha="center", va="center", family="monospace")
    ax.text(0.5, 0.16, f"CEP50 {cep50:.2f} m  ·  {mode_str}",
            transform=ax.transAxes, fontsize=9, color=_LABEL, ha="center", va="center", family="monospace")


def build_dashboard_text(
    mission_state,
    advisory_result,
    active_threshold_percent,
    active_mode,
):
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
