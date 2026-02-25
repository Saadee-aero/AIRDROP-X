"""
AX-FRAGILITY-SURFACE-20: Decision fragility surface.
Margin and slope-based zone classification (EDGE / TRANSITION / STABLE).
AX-FRAGILITY-HARDEN-23: Smoothed gradient for LIVE, hysteresis band.
"""

from __future__ import annotations

from typing import Any


def _run_wind_perturbed(
    config: dict,
    mode: str,
    mc_call_counter: list | None = None,
) -> float:
    """Run with wind +0.5 m/s, return P_hit. AX-MC-CALL-TRACE-25."""
    from adapter import run_simulation_snapshot

    cfg = dict(config)
    wx = float(cfg.get("wind_x", cfg.get("wind_mean_x", 0.0)))
    cfg["wind_x"] = wx + 0.5
    cfg.pop("simulation_fidelity", None)
    snap = run_simulation_snapshot(
        config_override=cfg,
        include_advisory=False,
        caller="FRAGILITY",
        trace_mode=mode,
        mc_call_counter=mc_call_counter,
    )
    return float(snap.get("P_hit", 0.0) or 0.0)


def _classify_zone(margin_pct: float, slope_margin: float) -> str:
    """AX-FRAGILITY-HARDEN-23: Classify zone with hysteresis band (margin-only)."""
    if margin_pct < 1.5:
        return "EDGE-ZONE"
    if margin_pct >= 5.0:
        return "STABLE-ZONE"
    return "TRANSITION-ZONE"


def compute_fragility(
    snapshot: dict[str, Any],
    config: dict[str, Any],
    mode: str,
    mc_call_counter: list | None = None,
) -> None:
    """
    AX-FRAGILITY-SURFACE-20: Add fragility_state to snapshot (mutates in place).

    Args:
        snapshot: Evaluation result (must have P_hit, threshold_pct).
        config: Full config dict.
        mode: "standard" (LIVE-equivalent) or "advanced" (ANALYTICAL-equivalent)
    """
    P_base = float(snapshot.get("P_hit", 0.0) or 0.0)
    threshold_pct = float(snapshot.get("threshold_pct", 75.0) or 75.0)
    threshold = threshold_pct / 100.0
    margin_frac = P_base - threshold
    margin_pct = margin_frac * 100.0

    dW = 0.5
    if mode == "standard":
        sens_live = snapshot.get("sensitivity_live") or {}
        g_smoothed = sens_live.get("wind_gradient_smoothed")
        if g_smoothed is not None:
            slope_margin = float(g_smoothed)
        else:
            P_perturbed = _run_wind_perturbed(config, mode, mc_call_counter)
            margin_perturbed_frac = P_perturbed - threshold
            slope_margin = (margin_perturbed_frac - margin_frac) / dW if dW != 0 else 0.0
    else:
        sens = snapshot.get("sensitivity_matrix") or {}
        dP_dW = float(sens.get("wind", 0.0) or 0.0)
        P_perturbed = P_base + dP_dW * dW
        margin_perturbed_frac = P_perturbed - threshold
        slope_margin = (margin_perturbed_frac - margin_frac) / dW if dW != 0 else 0.0

    zone = _classify_zone(margin_pct, slope_margin)
    snapshot["fragility_state"] = {
        "margin_pct": margin_pct,
        "slope_margin": slope_margin,
        "zone": zone,
    }
