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
    # Initial generic payload from config (as Library is now dynamic)
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
# (No content to replace. I am deleting lines. Wait, I should not leave it empty if I select specific lines. 
# I will just replace the block with nothing or a comment.)
# Cleaning up legacy code block.


def run_simulation(payload_config=None):
    """
    Run the full simulation loop.
    If payload_config is provided (dict), use it to create the Payload.
    Otherwise, use default from configs.
    """
    print(f"\\n--- Starting Simulation ---")
    if payload_config:
        print(f"Using Custom Payload: {payload_config.get('name', 'Unknown')}")
        mass = payload_config.get("mass", 5.0)
        cd = payload_config.get("drag_coefficient", 0.5)
        area = payload_config.get("reference_area", 0.01)
        # Reconstruct Payload object
        payload = Payload(mass=mass, drag_coefficient=cd, reference_area=area)
    else:
        # Default
        payload = Payload(
            mass=cfg.payload.mass_kg,
            drag_coefficient=cfg.payload.drag_coefficient,
            reference_area=cfg.payload.area_m2
        )

    # Initialize Other Components
    target = Target(
        position=cfg.target.position,
        radius=cfg.target.radius_m
    )
    
    # Environment
    env = Environment() 
    
    # Mission State
    state = MissionState(
        payload=payload,
        target=target,
        environment=env
    )
    
    # Run Landing Point Estimator (LPE)
    from product.lpe.lpe_core import get_impact_points
    impact_points = get_impact_points(state, n_samples=50) 
    
    # Evaluate Advisory
    advisory_result = evaluate_advisory(impact_points, target)
    print(f"Advisory: {advisory_result.current_feasibility}")
    
    # Calculate Metrics
    from product.lpe.lpe_core import calculate_cep50, calculate_hit_probability
    cep50 = calculate_cep50(impact_points, target.position)
    p_hit = calculate_hit_probability(impact_points, target)
    
    print(f"  -> CEP50: {cep50:.2f} m")
    print(f"  -> P(Hit): {p_hit*100:.1f} %")
    return impact_points, advisory_result


def main():
    # Initial Default Run
    impacts, adv = run_simulation()
    
    # Calculate initial display metrics
    # Re-calc for initial (or return from run_sim)
    cep50 = calculate_cep50(impacts, cfg.target.position)
    p_hit = calculate_hit_probability(impacts, Target(cfg.target.position, cfg.target.radius_m))

    # Launch UI
    # We pass 'run_simulation' as the callback.
    # Note: The UI callback expects to trigger logic.
    launch_unified_ui(
        impact_points=impacts,
        P_hit=p_hit,
        cep50=cep50,
        target_position=cfg.target.position,
        target_radius=cfg.target.radius_m,
        mission_state=None, # simplified
        advisory_result=adv,
        initial_threshold_percent=cfg.constraints.max_wind_speed_m_s, # Placeholder mapping
        initial_mode="standard",
        slider_min=0, slider_max=20, slider_step=1,
        mode_thresholds={},
        on_threshold_change=lambda x: None,
        random_seed=42,
        n_samples=50,
        dt=0.1,
        run_simulation_callback=run_simulation # <--- NEW
    )

if __name__ == "__main__":
    main()
