"""
Numerical diagnostics utilities for AIRDROP-X.
These checks are advisory and do not modify engine logic.
"""

from __future__ import annotations

from typing import Dict, Any


def quick_stability_check(
    random_seed: int,
    dt: float,
    samples: int = 5,
) -> Dict[str, Any]:
    """
    Compare CEP50 at dt and dt/2 over a small sample set.
    PASS when relative error < 2%, else CAUTION.
    """
    from configs import mission_configs as cfg
    from src import monte_carlo, metrics

    n = int(samples)
    dt_base = float(dt)
    dt_half = dt_base / 2.0 if dt_base > 0 else dt_base

    impact_dt = monte_carlo.run_monte_carlo(
        cfg.uav_pos,
        cfg.uav_vel,
        cfg.mass,
        cfg.Cd,
        cfg.A,
        cfg.rho,
        cfg.wind_mean,
        cfg.wind_std,
        n,
        random_seed,
        dt=dt_base,
    )
    impact_half = monte_carlo.run_monte_carlo(
        cfg.uav_pos,
        cfg.uav_vel,
        cfg.mass,
        cfg.Cd,
        cfg.A,
        cfg.rho,
        cfg.wind_mean,
        cfg.wind_std,
        n,
        random_seed,
        dt=dt_half,
    )

    cep_dt = metrics.compute_cep50(impact_dt, cfg.target_pos)
    cep_half = metrics.compute_cep50(impact_half, cfg.target_pos)
    denom = max(abs(cep_half), 1e-9)
    rel_err = abs(cep_dt - cep_half) / denom
    status = "PASS" if rel_err < 0.02 else "CAUTION"

    return {
        "integration_method": "Explicit Euler",
        "dt": dt_base,
        "samples": n,
        "relative_error": float(rel_err),
        "status": status,
    }

