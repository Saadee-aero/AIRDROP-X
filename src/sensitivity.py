"""
AX-SENSITIVITY-HYBRID-09: Hybrid sensitivity intelligence.
Optional sensitivity computation after main evaluation.
AX-LIVE-GRADIENT-SMOOTH-11: Exponential smoothing for LIVE wind gradient.
AX-SENSITIVITY-STATE-PURITY-13: Smoothing state owned by controller, not module.
"""

from __future__ import annotations

from typing import Any


def _run_perturbed(
    config: dict,
    perturb: dict,
    mode: str,
    mc_call_counter: list | None = None,
) -> float:
    """Run evaluation with perturbed config, return P_hit. Disables nested sensitivity. AX-MC-CALL-TRACE-25."""
    from adapter import run_simulation_snapshot

    cfg = dict(config)
    cfg.update(perturb)
    cfg.pop("simulation_fidelity", None)  # Avoid nested sensitivity runs
    snap = run_simulation_snapshot(
        config_override=cfg,
        include_advisory=False,
        caller="SENSITIVITY",
        trace_mode=mode,
        mc_call_counter=mc_call_counter,
    )
    return float(snap.get("P_hit", 0.0) or 0.0)


def _wind_sensitivity_level(dP_dW: float) -> str:
    """Map gradient to High / Moderate / Low."""
    abs_g = abs(dP_dW)
    if abs_g >= 0.05:
        return "High"
    if abs_g >= 0.02:
        return "Moderate"
    return "Low"


def compute_sensitivity(
    snapshot: dict[str, Any],
    config: dict[str, Any],
    mode: str,
    previous_wind_gradient: float | None = None,
    mc_call_counter: list | None = None,
) -> float | None:
    """
    AX-SENSITIVITY-HYBRID-09: Add sensitivity fields to snapshot (mutates in place).

    Args:
        snapshot: Base evaluation result (must have P_hit).
        config: Full config dict (wind_x, uav_altitude, uav_vx, n_samples, etc).
        mode: "standard" (LIVE-equivalent) or "advanced" (ANALYTICAL-equivalent)
        previous_wind_gradient: For standard mode, smoothed gradient from prior cycle.

    Returns:
        For standard: updated (smoothed) wind gradient.
        For advanced: None.
    """
    P_base = float(snapshot.get("P_hit", 0.0) or 0.0)
    cfg = dict(config)
    n_orig = int(cfg.get("n_samples", 1000))

    if mode == "standard":
        # Perturb wind magnitude by +0.5 m/s (along wind_x for simplicity)
        wx = float(cfg.get("wind_x", cfg.get("wind_mean_x", 0.0)))
        perturb = {
            "wind_x": wx + 0.5,
            "n_samples": max(30, int(n_orig * 0.3)),
        }
        P_perturbed = _run_perturbed(cfg, perturb, mode, mc_call_counter)
        dP_dW = (P_perturbed - P_base) / 0.5 if 0.5 != 0 else 0.0

        # AX-LIVE-GRADIENT-SMOOTH-11: exponential smoothing
        alpha = 0.3
        if previous_wind_gradient is not None:
            g_smoothed = alpha * dP_dW + (1 - alpha) * previous_wind_gradient
        else:
            g_smoothed = dP_dW

        snapshot["sensitivity_live"] = {
            "wind_gradient_raw": dP_dW,
            "wind_gradient_smoothed": g_smoothed,
            "wind_gradient": g_smoothed,  # backward compat for consumers
            "wind_sensitivity": _wind_sensitivity_level(g_smoothed),
        }
        return g_smoothed

    if mode == "advanced":
        # Perturb wind +0.5, altitude +5 m, velocity +2 m/s; full n_samples
        wx = float(cfg.get("wind_x", cfg.get("wind_mean_x", 0.0)))
        alt = float(cfg.get("uav_altitude", 100.0))
        vx = float(cfg.get("uav_vx", 20.0))

        P_w = _run_perturbed(cfg, {"wind_x": wx + 0.5}, mode, mc_call_counter)
        P_h = _run_perturbed(cfg, {"uav_altitude": alt + 5.0}, mode, mc_call_counter)
        P_v = _run_perturbed(cfg, {"uav_vx": vx + 2.0}, mode, mc_call_counter)

        dP_dW = (P_w - P_base) / 0.5 if 0.5 != 0 else 0.0
        dP_dH = (P_h - P_base) / 5.0 if 5.0 != 0 else 0.0
        dP_dV = (P_v - P_base) / 2.0 if 2.0 != 0 else 0.0

        matrix = {
            "wind": dP_dW,
            "altitude": dP_dH,
            "velocity": dP_dV,
        }
        ranked = sorted(
            [("wind", abs(dP_dW)), ("altitude", abs(dP_dH)), ("velocity", abs(dP_dV))],
            key=lambda x: -x[1],
        )
        snapshot["sensitivity_matrix"] = matrix
        snapshot["dominant_risk_factor"] = ranked[0][0] if ranked else "wind"
        return None
