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
) -> Dict[str, Any]:
    """Run one simulation snapshot using existing engine pipeline."""
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
    try:
        impact_points, P_hit, cep50, impact_velocity_stats = get_impact_points_and_metrics(
            mission_state, random_seed
        )
    finally:
        cfg.n_samples = saved_n_samples

    advisory_result = None
    if include_advisory:
        advisory_result = evaluate_advisory(
            mission_state,
            threshold_pct / 100.0,
            random_seed=random_seed,
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

    return {
        "impact_points": impact_points,
        "P_hit": P_hit,
        "cep50": cep50,
        "target_position": mission_state.target.position,
        "target_radius": mission_state.target.radius,
        "advisory": advisory_result,
        "wind_vector": tuple(wind_mean[:2]),
        "impact_velocity_stats": impact_velocity_stats,
        "snapshot_id": datetime.now().strftime("AX-%Y%m%d-%H%M%S"),
        "confidence_index": confidence_index,
    }
