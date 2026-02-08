from configs import mission_configs as cfg
from src import decision_logic
from product.payloads.payload_base import Payload
from product.missions.target_manager import Target
from product.missions.environment import Environment
from product.missions.mission_state import MissionState
from product.guidance.advisory_layer import (
    get_impact_points_and_metrics,
    evaluate_advisory,
)
from product.ui.ui_layout import launch_unified_ui

if __name__ == "__main__":
    payload = Payload(
        mass=cfg.mass,
        drag_coefficient=cfg.Cd,
        reference_area=cfg.A,
    )
    target = Target(position=cfg.target_pos, radius=cfg.target_radius)
    environment = Environment(
        wind_mean=cfg.wind_mean,
        wind_std=cfg.wind_std,
    )
    mission_state = MissionState(
        payload=payload,
        target=target,
        environment=environment,
        uav_position=cfg.uav_pos,
        uav_velocity=cfg.uav_vel,
    )
    impact_points, P_hit, cep50 = get_impact_points_and_metrics(
        mission_state,
        cfg.RANDOM_SEED,
    )
    advisory_result = evaluate_advisory(
        mission_state,
        cfg.THRESHOLD_SLIDER_INIT / 100.0,
        random_seed=cfg.RANDOM_SEED,
    )
    simulation_results = {
        "impact_points": impact_points,
        "P_hit": P_hit,
        "cep50": cep50,
        "target_position": mission_state.target.position,
        "target_radius": mission_state.target.radius,
        "mission_state": mission_state,
        "advisory_result": advisory_result,
        "initial_threshold_percent": cfg.THRESHOLD_SLIDER_INIT,
        "initial_mode": "Balanced",
        "slider_min": cfg.THRESHOLD_SLIDER_MIN,
        "slider_max": cfg.THRESHOLD_SLIDER_MAX,
        "slider_step": cfg.THRESHOLD_SLIDER_STEP,
        "mode_thresholds": cfg.MODE_THRESHOLDS,
    }
    r = simulation_results
    on_threshold_change = lambda t: decision_logic.evaluate_drop_decision(r["P_hit"], t)
    launch_unified_ui(
        r["impact_points"],
        r["P_hit"],
        r["cep50"],
        r["target_position"],
        r["target_radius"],
        r["mission_state"],
        r["advisory_result"],
        r["initial_threshold_percent"],
        r["initial_mode"],
        r["slider_min"],
        r["slider_max"],
        r["slider_step"],
        r["mode_thresholds"],
        on_threshold_change,
    )
