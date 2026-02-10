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


def _build_mission_state(payload_config=None):
    """
    Build a MissionState from config defaults, optionally overriding payload
    with a custom dict from the Dynamic Payload Builder.
    """
    if payload_config:
        payload = Payload(
            mass=payload_config.get("mass", cfg.mass),
            drag_coefficient=payload_config.get("drag_coefficient", cfg.Cd),
            reference_area=payload_config.get("reference_area", cfg.A),
        )
    else:
        payload = Payload(
            mass=cfg.mass,
            drag_coefficient=cfg.Cd,
            reference_area=cfg.A,
        )

    target = Target(position=cfg.target_pos, radius=cfg.target_radius)
    environment = Environment(wind_mean=cfg.wind_mean, wind_std=cfg.wind_std)

    return MissionState(
        payload=payload,
        target=target,
        environment=environment,
        uav_position=cfg.uav_pos,
        uav_velocity=cfg.uav_vel,
    )


def run_simulation(payload_config=None):
    """
    Run the full simulation loop.
    If payload_config is provided (dict from Payload Builder), use it.
    Otherwise, use defaults from configs.mission_configs.
    Returns (impact_points, advisory_result).
    """
    print(f"\n--- Starting Simulation ---")
    if payload_config:
        print(f"Using Custom Payload: {payload_config.get('name', 'Unknown')}")

    mission_state = _build_mission_state(payload_config)

    # Run Monte Carlo + metrics
    impact_points, P_hit, cep50 = get_impact_points_and_metrics(
        mission_state, cfg.RANDOM_SEED
    )

    # Evaluate advisory (directional analysis)
    advisory_result = evaluate_advisory(
        mission_state, "Balanced", random_seed=cfg.RANDOM_SEED
    )

    print(f"  -> CEP50: {cep50:.2f} m")
    print(f"  -> P(Hit): {P_hit*100:.1f} %")
    print(f"  -> Advisory: {advisory_result.current_feasibility}")

    return impact_points, advisory_result, P_hit, cep50


def main():
    """Entry point: run simulation and launch UI."""
    impacts, adv, p_hit, cep50 = run_simulation()

    launch_unified_ui(
        impact_points=impacts,
        P_hit=p_hit,
        cep50=cep50,
        target_position=cfg.target_pos,
        target_radius=cfg.target_radius,
        mission_state=None,
        advisory_result=adv,
        initial_threshold_percent=cfg.THRESHOLD_SLIDER_INIT,
        initial_mode="standard",
        slider_min=cfg.THRESHOLD_SLIDER_MIN,
        slider_max=cfg.THRESHOLD_SLIDER_MAX,
        slider_step=cfg.THRESHOLD_SLIDER_STEP,
        mode_thresholds=cfg.MODE_THRESHOLDS,
        on_threshold_change=lambda x: None,
        random_seed=cfg.RANDOM_SEED,
        n_samples=cfg.n_samples,
        dt=cfg.dt,
        run_simulation_callback=run_simulation,
    )


if __name__ == "__main__":
    main()
