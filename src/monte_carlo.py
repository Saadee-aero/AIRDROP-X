import numpy as np
from src import physics


def _draw_wind_sample(rng, wind_mean, wind_std):
    """Draw one wind vector (3,) from Gaussian. SI: m/s."""
    wind_mean = np.asarray(wind_mean, dtype=float).reshape(3)
    return wind_mean + rng.normal(0, wind_std, size=3)


def _impact_xy(trajectory):
    """Extract final (x, y) from trajectory (N, 3). Returns (2,) or None if empty."""
    if trajectory.shape[0] == 0:
        return None
    return trajectory[-1, :2].copy()


def run_monte_carlo(
    pos0,
    vel0,
    mass,
    Cd,
    A,
    rho,
    wind_mean,
    wind_std,
    n_samples,
    random_seed,
    dt=0.01,
    return_trajectories=False,
):
    """
    Monte Carlo uncertainty propagation. One wind sample per trajectory.
    Same seed gives same results. Returns impact points (N, 2); optionally full trajectories.
    All inputs explicit. SI units.
    """
    pos0 = np.asarray(pos0, dtype=float).reshape(3)
    vel0 = np.asarray(vel0, dtype=float).reshape(3)
    wind_mean = np.asarray(wind_mean, dtype=float).reshape(3)
    rng = np.random.default_rng(seed=random_seed)

    impact_points = []
    trajectories_out = [] if return_trajectories else None

    for _ in range(n_samples):
        wind = _draw_wind_sample(rng, wind_mean, wind_std)
        trajectory = physics.propagate_payload(
            pos0, vel0, mass, Cd, A, rho, wind, dt
        )
        xy = _impact_xy(trajectory)
        if xy is None:
            xy = np.array([pos0[0], pos0[1]], dtype=float)
        impact_points.append(xy)
        if return_trajectories:
            trajectories_out.append(trajectory)

    impact_array = np.array(impact_points, dtype=float).reshape(n_samples, 2)
    if return_trajectories:
        return impact_array, trajectories_out
    return impact_array
