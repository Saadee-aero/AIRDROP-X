"""
Monte Carlo uncertainty propagation — batch vectorized engine.
Same physics as propagate_payload; all samples computed in parallel.
"""
import time
import numpy as np
from src import physics


# Gravity vector (SI) — matches physics.GRAVITY_MAGNITUDE
_GRAVITY = np.array([0.0, 0.0, -9.81], dtype=float)


def _draw_wind_sample(rng, wind_mean, wind_std):
    """Draw one wind vector (3,) from Gaussian. SI: m/s."""
    wind_mean = np.asarray(wind_mean, dtype=float).reshape(3)
    return wind_mean + rng.normal(0, wind_std, size=3)


def _draw_wind_batch(rng, wind_mean, wind_std, n_samples):
    """Draw N wind vectors (N, 3) from Gaussian. SI: m/s. Deterministic for same seed."""
    wind_mean = np.asarray(wind_mean, dtype=float).reshape(3)
    return wind_mean + rng.normal(0, wind_std, size=(n_samples, 3))


def _impact_xy(trajectory):
    """Extract final (x, y) from trajectory (N, 3). Returns (2,) or None if empty."""
    if trajectory.shape[0] == 0:
        return None
    return trajectory[-1, :2].copy()


def _impact_speed(trajectory, dt, pos0, vel0):
    """Compute impact velocity magnitude from trajectory (post-processing only)."""
    if trajectory.shape[0] == 0:
        return float(np.linalg.norm(vel0))
    if trajectory.shape[0] >= 2:
        disp = trajectory[-1] - trajectory[-2]
        return float(np.linalg.norm(disp / dt))
    return float(np.linalg.norm(vel0))


def _propagate_payload_batch(
    pos0, vel0, mass, Cd, A, rho, wind_samples, dt,
    return_trajectories=False,
    return_impact_speeds=False,
):
    """
    Batch vectorized propagation. Same physics as propagate_payload.
    pos0, vel0: (3,). wind_samples: (N, 3).
    Returns impact_xy (N, 2), optionally trajectories list, impact_speeds (N,).
    Single integration loop; no per-sample Python loop.
    """
    N = wind_samples.shape[0]
    pos = np.broadcast_to(np.asarray(pos0, dtype=float).reshape(3), (N, 3)).copy()
    vel = np.broadcast_to(np.asarray(vel0, dtype=float).reshape(3), (N, 3)).copy()

    impact_xy = np.full((N, 2), np.asarray(pos0)[:2], dtype=float)
    impact_stored = np.zeros(N, dtype=bool)

    impact_speeds_out = np.zeros(N, dtype=float) if return_impact_speeds else None

    # Trajectory buffer: (max_steps, N, 3). Conservative for ~100m, dt=0.01.
    max_steps = 25000
    traj = np.zeros((max_steps, N, 3), dtype=float) if return_trajectories else None
    step_count = np.zeros(N, dtype=int) if return_trajectories else None

    step = 0
    active = pos[:, 2] > 0

    while np.any(active):
        # --- Physics: v_rel, drag, acc (only for active) ---
        v_rel = vel[active] - wind_samples[active]
        v_rel_mag = np.linalg.norm(v_rel, axis=1)

        # F_drag = -0.5 * rho * Cd * A * |v_rel| * v_rel; zero when |v_rel|=0
        drag_force = np.where(
            v_rel_mag[:, None] > 0,
            -0.5 * rho * Cd * A * v_rel_mag[:, None] * v_rel,
            0.0,
        )
        acc = _GRAVITY + drag_force / mass

        # Semi-implicit Euler: vel then pos (same as propagate_payload)
        vel[active] = vel[active] + acc * dt
        pos[active] = pos[active] + vel[active] * dt

        # --- Store trajectories if requested ---
        if return_trajectories and step < max_steps:
            traj[step, active, :] = pos[active]
            step_count[active] = step + 1

        # --- Detect ground impact ---
        active_new = pos[:, 2] > 0
        just_hit = active & ~active_new

        impact_xy[just_hit, 0] = pos[just_hit, 0]
        impact_xy[just_hit, 1] = pos[just_hit, 1]
        impact_stored[just_hit] = True

        if return_impact_speeds:
            impact_speeds_out[just_hit] = np.linalg.norm(vel[just_hit], axis=1)

        active = active_new
        step += 1

        if return_trajectories and step >= max_steps:
            remaining = active.copy()
            impact_xy[remaining] = pos[remaining, :2]
            impact_stored[remaining] = True
            if return_impact_speeds:
                impact_speeds_out[remaining] = np.linalg.norm(vel[remaining], axis=1)
            break

    # Fallback for samples that never hit (e.g. z0<=0)
    impact_xy[~impact_stored] = np.asarray(pos0)[:2]

    if return_trajectories:
        trajectories_out = [
            traj[: step_count[i], i, :].copy() for i in range(N)
        ]
        return (impact_xy, trajectories_out, impact_speeds_out)

    return (impact_xy, impact_speeds_out)


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
    return_impact_speeds=False,
):
    """
    Monte Carlo uncertainty propagation. One wind sample per trajectory.
    Same seed gives same results. Returns impact points (N, 2);
    optionally full trajectories. When return_impact_speeds=True,
    also returns impact_speeds (N,) in m/s. All inputs explicit. SI units.

    Implementation: batch vectorized. No Python loop over samples.
    Complexity O(S) with S = integration steps (vs O(N*S) previously).
    """
    pos0 = np.asarray(pos0, dtype=float).reshape(3)
    vel0 = np.asarray(vel0, dtype=float).reshape(3)
    wind_mean = np.asarray(wind_mean, dtype=float).reshape(3)
    rng = np.random.default_rng(seed=random_seed)

    t0 = time.perf_counter()

    # --- Batch wind samples (N, 3) ---
    wind_samples = _draw_wind_batch(rng, wind_mean, wind_std, n_samples)

    # --- Batch propagation ---
    result = _propagate_payload_batch(
        pos0, vel0, mass, Cd, A, rho, wind_samples, dt,
        return_trajectories=return_trajectories,
        return_impact_speeds=return_impact_speeds,
    )

    t_ms = (time.perf_counter() - t0) * 1000.0
    print(f"[Monte Carlo] N={n_samples} elapsed={t_ms:.2f} ms")

    impact_array = result[0].reshape(n_samples, 2)

    if return_trajectories:
        trajectories_out = result[1]
        impact_speeds_out = result[2]
        if return_impact_speeds:
            return impact_array, trajectories_out, impact_speeds_out
        return impact_array, trajectories_out

    if return_impact_speeds:
        return impact_array, result[1]

    return impact_array
