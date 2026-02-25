"""
AX-RELEASE-CORRIDOR-19: Release corridor intelligence.
Region along longitudinal axis where P_hit >= threshold.
AX-RELEASE-CORRIDOR-HARDEN-22: Tolerance and resolution safeguard.
"""

from __future__ import annotations

from typing import Any


def _run_at_offset(
    config: dict,
    dx: float,
    mode: str,
    mc_call_counter: list | None = None,
) -> float:
    """Run evaluation with uav_x offset by dx meters. Returns P_hit. AX-MC-CALL-TRACE-25."""
    from configs import mission_configs as mcfg
    from adapter import run_simulation_snapshot

    cfg = dict(config)
    x0 = float(cfg.get("uav_x", mcfg.uav_pos[0]))
    cfg["uav_x"] = x0 + dx
    cfg.pop("simulation_fidelity", None)
    cfg.pop("uav_pos", None)
    caller = "CORRIDOR_LEFT" if dx < 0 else "CORRIDOR_RIGHT"
    snap = run_simulation_snapshot(
        config_override=cfg,
        include_advisory=False,
        caller=caller,
        trace_mode=mode,
        mc_call_counter=mc_call_counter,
    )
    return float(snap.get("P_hit", 0.0) or 0.0)


def compute_release_corridor(
    snapshot: dict[str, Any],
    config: dict[str, Any],
    mode: str,
    mc_call_counter: list | None = None,
) -> None:
    """
    AX-RELEASE-CORRIDOR-19: Add release corridor fields to snapshot (mutates in place).

    Args:
        snapshot: Evaluation result (must have P_hit, threshold_pct).
        config: Full config dict (uav_x, n_samples, etc).
        mode: "standard" (LIVE-equivalent) or "advanced" (ANALYTICAL-equivalent)
    """
    P_base = float(snapshot.get("P_hit", 0.0) or 0.0)
    threshold_pct = float(snapshot.get("threshold_pct", 75.0) or 75.0)
    threshold = threshold_pct / 100.0
    epsilon_pct = 0.5
    threshold_eff = threshold - (epsilon_pct / 100.0)
    cfg = dict(config)
    n_orig = int(cfg.get("n_samples", 1000))
    dx = 1.0

    if mode == "standard":
        n_reduced = max(30, int(n_orig * 0.3))
        cfg_reduced = dict(cfg)
        cfg_reduced["n_samples"] = n_reduced

        P_minus = _run_at_offset(cfg_reduced, -dx, mode, mc_call_counter)
        P_plus = _run_at_offset(cfg_reduced, dx, mode, mc_call_counter)

        both_ok = (P_minus >= threshold_eff) and (P_plus >= threshold_eff)
        one_ok = (P_minus >= threshold_eff) or (P_plus >= threshold_eff)

        if both_ok:
            corridor_width_m = 2.0 * dx
        elif one_ok:
            corridor_width_m = dx
        else:
            corridor_width_m = 0.0

        margin_pct = (P_base - threshold) * 100.0
        snapshot["release_corridor_live"] = {
            "corridor_width_m": corridor_width_m,
            "margin_pct": margin_pct,
        }
        return

    if mode == "advanced":
        offsets = list(range(-5, 6))
        p_hits = []
        for off in offsets:
            p = _run_at_offset(cfg, float(off), mode, mc_call_counter)
            p_hits.append((off, p))

        in_corridor = [(o, p) for o, p in p_hits if p >= threshold_eff]
        step_size = 1.0
        if not in_corridor:
            min_offset_m = 0.0
            max_offset_m = 0.0
            corridor_width_m = 0.0
        else:
            offsets_in = [o for o, _ in in_corridor]
            min_offset_m = float(min(offsets_in))
            max_offset_m = float(max(offsets_in))
            corridor_width_m = max_offset_m - min_offset_m
            if corridor_width_m > 0 and corridor_width_m < step_size:
                corridor_width_m = "<1.0"

        snapshot["release_corridor_matrix"] = {
            "min_offset_m": min_offset_m,
            "max_offset_m": max_offset_m,
            "corridor_width_m": corridor_width_m,
        }
        return
