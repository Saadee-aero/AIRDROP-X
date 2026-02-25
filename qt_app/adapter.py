"""Thin engine adapter for Qt UI snapshot simulation calls."""

from __future__ import annotations

from pathlib import Path
import sys
from datetime import datetime
from typing import Any, Dict


_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


def run_simulation_snapshot(
    config_override: Dict[str, Any] | None = None,
    include_advisory: bool = False,
    previous_wind_gradient: float | None = None,
    *,
    caller: str = "BASE",
    trace_mode: str | None = None,
    mc_call_counter: list | None = None,
) -> Dict[str, Any]:
    """Run one simulation snapshot using existing engine pipeline. AX-MC-CALL-TRACE-25."""
    from configs import mission_configs as cfg
    from product.payloads.payload_base import Payload
    from product.missions.target_manager import Target
    from product.missions.environment import Environment
    from product.missions.mission_state import MissionState
    from product.guidance.advisory_layer import (
        evaluate_advisory,
        get_impact_points_and_metrics,
    )

    overrides = dict(config_override or {})
    is_outer = mc_call_counter is None
    if mc_call_counter is None:
        mc_call_counter = [0]
    # Engine entry observability
    print("DISPLAY =", overrides.get("display_mode"))
    print("FIDELITY =", overrides.get("simulation_fidelity"))
    print("EXECUTION =", overrides.get("execution_mode"))
    mode = trace_mode if trace_mode is not None else str(overrides.get("simulation_fidelity", "advanced")).strip().lower() or "advanced"
    print(f"[ENGINE TRACE] mode={mode}")

    mass = float(overrides.get("mass", cfg.mass))
    cd = float(overrides.get("cd", cfg.Cd))
    area = float(overrides.get("area", cfg.A))

    uav_pos = (
        float(overrides.get("uav_x", cfg.uav_pos[0])),
        float(overrides.get("uav_y", cfg.uav_pos[1])),
        float(overrides.get("uav_altitude", cfg.uav_pos[2])),
    )
    uav_vel = (
        float(overrides.get("uav_vx", cfg.uav_vel[0])),
        float(overrides.get("uav_vy", cfg.uav_vel[1])),
        float(overrides.get("uav_vz", cfg.uav_vel[2])),
    )
    target_pos = (
        float(overrides.get("target_x", cfg.target_pos[0])),
        float(overrides.get("target_y", cfg.target_pos[1])),
    )
    target_radius = float(overrides.get("target_radius", cfg.target_radius))
    wind_mean = (
        float(overrides.get("wind_x", overrides.get("wind_mean_x", cfg.wind_mean[0]))),
        float(overrides.get("wind_y", overrides.get("wind_mean_y", cfg.wind_mean[1]))),
        float(cfg.wind_mean[2] if len(cfg.wind_mean) > 2 else 0.0),
    )
    wind_std = float(overrides.get("wind_std", cfg.wind_std))
    n_samples = int(overrides.get("n_samples", cfg.n_samples))
    random_seed = int(overrides.get("random_seed", cfg.RANDOM_SEED))
    threshold_pct = float(overrides.get("threshold_pct", cfg.THRESHOLD_SLIDER_INIT))

    payload = Payload(
        mass=mass,
        drag_coefficient=cd,
        reference_area=area,
    )
    target = Target(position=target_pos, radius=target_radius)
    environment = Environment(wind_mean=wind_mean, wind_std=wind_std)
    mission_state = MissionState(
        payload=payload,
        target=target,
        environment=environment,
        uav_position=uav_pos,
        uav_velocity=uav_vel,
    )

    saved_n_samples = cfg.n_samples
    cfg.n_samples = n_samples
    mc_call_counter[0] += 1
    try:
        impact_points, P_hit, cep50, impact_velocity_stats = get_impact_points_and_metrics(
            mission_state, random_seed, caller=caller, mode=mode
        )
    finally:
        cfg.n_samples = saved_n_samples

    advisory_result = None
    if include_advisory:
        print(f"[ADVISORY TRACE] EXECUTING SWEEP in mode={mode}")
        advisory_result = evaluate_advisory(
            mission_state,
            threshold_pct / 100.0,
            random_seed=random_seed,
            trace_mode=mode,
        )

    # Confidence index for Mission Overview banner
    from src import metrics
    bc = (mass / (cd * area)) if (cd and area) else None
    confidence_index = metrics.compute_confidence_index(
        wind_std=wind_std,
        ballistic_coefficient=bc,
        altitude=uav_pos[2],
        telemetry_freshness=None,
    )

    # True integer hit count (same logic as metrics.compute_hit_probability)
    import numpy as np
    impact_arr = np.asarray(impact_points, dtype=float)
    if impact_arr.size > 0 and impact_arr.ndim == 2 and impact_arr.shape[1] >= 2:
        target_2d = np.asarray(mission_state.target.position, dtype=float).reshape(2)
        radial_distances = np.linalg.norm(impact_arr[:, :2] - target_2d, axis=1)
        hits = int(np.sum(radial_distances <= mission_state.target.radius))
        n_actual = int(impact_arr.shape[0])
        P_hit = float(hits) / float(n_actual) if n_actual > 0 else 0.0
    else:
        hits = 0
        n_actual = n_samples
        P_hit = 0.0

    # Telemetry-like dict for unified Control Center rendering (SNAPSHOT path)
    telemetry = {
        "x": uav_pos[0],
        "y": uav_pos[1],
        "z": uav_pos[2],
        "vx": uav_vel[0],
        "vy": uav_vel[1],
        "wind_x": wind_mean[0],
        "wind_y": wind_mean[1] if len(wind_mean) > 1 else 0.0,
        "wind_std": wind_std,
    }
    # Wilson CI and doctrine for SNAPSHOT path (uses true integer hits)
    from src.statistics import compute_wilson_ci
    from src.decision_doctrine import evaluate_doctrine, DOCTRINE_DESCRIPTIONS
    ci_low, ci_high = compute_wilson_ci(hits, n_actual)
    doctrine = str(overrides.get("doctrine_mode", "BALANCED")).strip().upper()
    doctrine_result = evaluate_doctrine(
        p_hat=P_hit,
        ci_low=ci_low,
        ci_high=ci_high,
        threshold=threshold_pct / 100.0,
        doctrine=doctrine,
        n_samples=n_actual,
    )
    result = {
        "impact_points": impact_points,
        "hits": hits,
        "P_hit": P_hit,
        "cep50": cep50,
        "target_position": mission_state.target.position,
        "target_radius": mission_state.target.radius,
        "advisory": advisory_result,
        "wind_vector": tuple(wind_mean[:2]),
        "impact_velocity_stats": impact_velocity_stats,
        "snapshot_id": datetime.now().strftime("AX-%Y%m%d-%H%M%S"),
        "confidence_index": confidence_index,
        "telemetry": telemetry,
        "n_samples": n_actual,
        "random_seed": random_seed,
        "threshold_pct": threshold_pct,
        "ci_low": ci_low,
        "ci_high": ci_high,
        "p_hat": P_hit,
        "decision": doctrine_result["decision"],
        "decision_reason": doctrine_result["reason"],
        "doctrine_mode": doctrine,
        "doctrine_description": doctrine_result.get("doctrine_description") or DOCTRINE_DESCRIPTIONS.get(doctrine, doctrine),
    }

    # AX-SENSITIVITY-HYBRID-09: optional sensitivity computation
    simulation_fidelity = str(overrides.get("simulation_fidelity", "")).strip().lower()
    if simulation_fidelity in ("standard", "advanced"):
        try:
            from src.sensitivity import compute_sensitivity

            updated_gradient = compute_sensitivity(
                result, overrides, simulation_fidelity,
                previous_wind_gradient=previous_wind_gradient,
                mc_call_counter=mc_call_counter,
            )
            if updated_gradient is not None:
                result["updated_wind_gradient"] = updated_gradient
        except Exception:
            pass  # Non-fatal; snapshot remains valid

    # AX-MISS-TOPOLOGY-HYBRID-12: topology layer (after sensitivity, before emission)
    if simulation_fidelity in ("standard", "advanced"):
        try:
            from src.topology import compute_topology

            compute_topology(result, simulation_fidelity)
        except Exception:
            pass  # Non-fatal; snapshot remains valid

    # AX-RELEASE-CORRIDOR-19: release corridor (after topology)
    if simulation_fidelity in ("standard", "advanced"):
        try:
            from src.release_corridor import compute_release_corridor

            compute_release_corridor(result, overrides, simulation_fidelity, mc_call_counter=mc_call_counter)
        except Exception:
            pass  # Non-fatal; snapshot remains valid

    # AX-FRAGILITY-SURFACE-20: fragility state (uses sensitivity when advanced fidelity)
    if simulation_fidelity in ("standard", "advanced"):
        try:
            from src.fragility import compute_fragility

            compute_fragility(result, overrides, simulation_fidelity, mc_call_counter=mc_call_counter)
        except Exception:
            pass  # Non-fatal; snapshot remains valid

    # AX-UNCERTAINTY-DECOMPOSITION-21: contribution weights (requires sensitivity_matrix)
    if simulation_fidelity == "advanced":
        try:
            from src.uncertainty_decomposition import compute_uncertainty_contribution

            compute_uncertainty_contribution(result)
        except Exception:
            pass  # Non-fatal; snapshot remains valid

    if is_outer:
        print(f"[MC SUMMARY] total_calls_this_cycle={mc_call_counter[0]}")

    return result
