"""
Product entry point. Runs the full product pipeline and launches the product UI.
main.py remains the research/engine validation entry point.
"""

import matplotlib.pyplot as plt

from product.payloads.payload_factory import create_payload
from product.missions.target_manager import Target
from product.missions.environment import Environment
from product.missions.mission_state import MissionState
from product.guidance.advisory_layer import (
    get_impact_points_and_metrics,
    evaluate_advisory,
)
from product.ui.dashboard import build_dashboard_figure
from product.ui.crosshair_view import figure_crosshair_view

RANDOM_SEED = 42
ACTIVE_MODE = "Balanced"
ACTIVE_THRESHOLD_PERCENT = 75.0


def main():
    payload = create_payload(
        "sphere",
        mass=0.5,
        radius=0.05,
    )
    target = Target(position=(72.0, 0.0), radius=5.0)
    environment = Environment(
        wind_mean=(2.0, 0.0, 0.0),
        wind_std=0.8,
    )
    uav_position = (0.0, 0.0, 100.0)
    uav_velocity = (20.0, 0.0, 0.0)

    mission_state = MissionState(
        payload=payload,
        target=target,
        environment=environment,
        uav_position=uav_position,
        uav_velocity=uav_velocity,
    )

    impact_points, P_hit, cep50 = get_impact_points_and_metrics(
        mission_state,
        RANDOM_SEED,
    )
    advisory_result = evaluate_advisory(
        mission_state,
        ACTIVE_MODE,
        random_seed=RANDOM_SEED,
    )

    build_dashboard_figure(
        mission_state,
        advisory_result,
        ACTIVE_THRESHOLD_PERCENT,
        ACTIVE_MODE,
    )
    figure_crosshair_view(
        impact_points,
        mission_state.target.position,
        mission_state.target.radius,
        cep50,
        advisory_result.current_feasibility,
    )
    plt.show()


if __name__ == "__main__":
    main()
