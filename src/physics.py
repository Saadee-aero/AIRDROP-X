import numpy as np
from configs import mission_configs as cfg


def propagate_trajectory(position_0, velocity_0, wind_vector):
    position = np.array(position_0, dtype=float).copy()
    velocity = np.array(velocity_0, dtype=float).copy()
    wind_vector = np.array(wind_vector, dtype=float)

    trajectory = []
    while position[2] > 0:
        relative_velocity = velocity - wind_vector
        relative_speed = np.linalg.norm(relative_velocity)

        if relative_speed > 0:
            drag_magnitude = 0.5 * cfg.rho * cfg.Cd * cfg.A * relative_speed ** 2
            drag_force = -drag_magnitude * (relative_velocity / relative_speed)
        else:
            drag_force = np.zeros(3)

        gravity = np.array([0.0, 0.0, -cfg.g])
        acceleration = gravity + drag_force / cfg.mass
        velocity = velocity + acceleration * cfg.dt
        position = position + velocity * cfg.dt
        trajectory.append(position.copy())

    if len(trajectory) == 0:
        return np.empty((0, 3))
    return np.array(trajectory, dtype=float).reshape(-1, 3)
