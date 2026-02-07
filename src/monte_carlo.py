import numpy as np
from configs import mission_configs as cfg
from src import physics


def run_simulation():
    position_0 = np.array(cfg.uav_pos, dtype=float)
    velocity_0 = np.array(cfg.uav_vel, dtype=float)
    wind_mean = np.array(cfg.wind_mean, dtype=float)
    n_samples = cfg.n_samples

    impact_points = []
    for _ in range(n_samples):
        wind_vector = wind_mean + np.random.normal(0, cfg.wind_std, size=3)
        trajectory = physics.propagate_trajectory(position_0, velocity_0, wind_vector)
        impact_xy = trajectory[-1, :2].copy()
        impact_points.append(impact_xy)

    return np.array(impact_points, dtype=float).reshape(n_samples, 2)
