import numpy as np
from configs import mission_configs as cfg
from src import monte_carlo
from src import metrics
from src import decision_logic
from src import ui

if __name__ == "__main__":
    np.random.seed(cfg.RANDOM_SEED)

    impact_points = monte_carlo.run_simulation()
    P_hit = metrics.compute_hit_probability(
        impact_points, cfg.target_pos, cfg.target_radius
    )
    cep50 = metrics.compute_cep50(impact_points, cfg.target_pos)

    initial_threshold = cfg.THRESHOLD_SLIDER_INIT / 100.0
    decision, effective_threshold = decision_logic.evaluate_drop_decision(
        P_hit, initial_threshold
    )

    ui.launch_ui(impact_points, P_hit, cep50)
