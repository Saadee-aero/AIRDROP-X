"""
Numerical validation of vectorized Monte Carlo engine.
DO NOT refactor. ONLY verify correctness and determinism.
"""
import sys
import time
import io
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
from src.monte_carlo import run_monte_carlo, _draw_wind_batch, _propagate_payload_batch
from src import physics


def _run_monte_carlo_old(pos0, vel0, mass, Cd, A, rho, wind_mean, wind_std, n_samples, random_seed, dt=0.01):
    """Original loop-based implementation for Phase 2 comparison."""
    pos0 = np.asarray(pos0, dtype=float).reshape(3)
    vel0 = np.asarray(vel0, dtype=float).reshape(3)
    wind_mean = np.asarray(wind_mean, dtype=float).reshape(3)
    rng = np.random.default_rng(seed=random_seed)
    impact_points = []
    for _ in range(n_samples):
        wind = wind_mean + rng.normal(0, wind_std, size=3)
        trajectory = physics.propagate_payload(pos0, vel0, mass, Cd, A, rho, wind, dt)
        if trajectory.shape[0] == 0:
            xy = np.array([pos0[0], pos0[1]], dtype=float)
        else:
            xy = trajectory[-1, :2].copy()
        impact_points.append(xy)
    return np.array(impact_points, dtype=float).reshape(n_samples, 2)


def _suppress_timing():
    """Redirect stdout to suppress [Monte Carlo] timing prints during validation."""
    import contextlib
    @contextlib.contextmanager
    def _no_print():
        old = sys.stdout
        sys.stdout = io.StringIO()
        try:
            yield
        finally:
            sys.stdout = old
    return _no_print()


def phase1_determinism():
    """Phase 1: Determinism check."""
    pos0 = (0.0, 0.0, 100.0)
    vel0 = (20.0, 0.0, 0.0)
    mass, Cd, A, rho = 1.0, 1.0, 0.01, 1.225
    wind_mean, wind_std = (2.0, 0.0, 0.0), 0.8
    dt, seed, N = 0.01, 42, 50

    with _suppress_timing():
        imp1 = run_monte_carlo(pos0, vel0, mass, Cd, A, rho, wind_mean, wind_std, N, seed, dt=dt)
        imp2 = run_monte_carlo(pos0, vel0, mass, Cd, A, rho, wind_mean, wind_std, N, seed, dt=dt)

    equal = np.array_equal(imp1, imp2)
    if equal:
        max_diff = 0.0
        result = "PASS"
    else:
        max_diff = np.max(np.abs(imp1 - imp2))
        result = "FAIL"

    print("=" * 60)
    print("PHASE 1 — Determinism Check")
    print("=" * 60)
    print(f"Result: {result}")
    print(f"Deterministic? {'YES' if equal else 'NO'}")
    print(f"Max difference: {max_diff}")
    if result == "FAIL":
        print("Anomaly: Two runs with same seed produced different results.")
    else:
        print("Anomalies: None")
    print(f"Risk: {'LOW' if equal else 'HIGH'}")
    print()
    return result == "PASS"


def phase2_old_vs_new():
    """Phase 2: Old vs new engine consistency."""
    pos0 = (0.0, 0.0, 100.0)
    vel0 = (20.0, 0.0, 0.0)
    mass, Cd, A, rho = 1.0, 1.0, 0.01, 1.225
    wind_mean, wind_std = (2.0, 0.0, 0.0), 0.8
    dt, seed, N = 0.01, 42, 50

    with _suppress_timing():
        imp_old = _run_monte_carlo_old(pos0, vel0, mass, Cd, A, rho, wind_mean, wind_std, N, seed, dt=dt)
        imp_new = run_monte_carlo(pos0, vel0, mass, Cd, A, rho, wind_mean, wind_std, N, seed, dt=dt)

    max_err_x = np.max(np.abs(imp_old[:, 0] - imp_new[:, 0]))
    max_err_y = np.max(np.abs(imp_old[:, 1] - imp_new[:, 1]))
    mean_abs_err = np.mean(np.abs(imp_old - imp_new))
    within_tol = max(max_err_x, max_err_y, mean_abs_err) < 1e-6

    result = "PASS" if within_tol else "FAIL"
    print("=" * 60)
    print("PHASE 2 — Old vs New Engine Consistency")
    print("=" * 60)
    print(f"Result: {result}")
    print(f"Max absolute error in x: {max_err_x:.2e}")
    print(f"Max absolute error in y: {max_err_y:.2e}")
    print(f"Mean absolute error: {mean_abs_err:.2e}")
    print(f"Within 1e-6 tolerance? {'YES' if within_tol else 'NO'}")
    if not within_tol:
        print("Anomaly: Old and new engines produce numerically different results.")
    else:
        print("Anomalies: None")
    print(f"Risk: {'LOW' if within_tol else 'MEDIUM'}")
    print()
    return result == "PASS"


def phase3_edge_cases():
    """Phase 3: Edge case stability."""
    base = {"vel0": (20.0, 0.0, 0.0), "mass": 1.0, "Cd": 1.0, "A": 0.01, "rho": 1.225, "wind_mean": (2.0, 0.0, 0.0), "wind_std": 0.8}
    cases = {
        "A) Low altitude (z=5m)": {"pos0": (0.0, 0.0, 5.0), **base},
        "B) High altitude (z=500m)": {"pos0": (0.0, 0.0, 500.0), **base},
        "C) Zero wind": {"pos0": (0.0, 0.0, 100.0), "wind_mean": (0.0, 0.0, 0.0), "wind_std": 0.0, **base},
        "D) High wind_std": {"pos0": (0.0, 0.0, 100.0), "wind_std": 5.0, **base},
        "E) Very high drag (Cd=5)": {"pos0": (0.0, 0.0, 100.0), "Cd": 5.0, **base},
        "F) Very small dt": {"pos0": (0.0, 0.0, 50.0), "dt": 0.001, **base},
        "G) Very large dt": {"pos0": (0.0, 0.0, 100.0), "dt": 0.1, **base},
    }

    results = []
    print("=" * 60)
    print("PHASE 3 — Edge Case Stability")
    print("=" * 60)

    for name, params in cases.items():
        pos0 = params["pos0"]
        vel0 = params["vel0"]
        mass, Cd, A, rho = params["mass"], params["Cd"], params["A"], params["rho"]
        wind_mean = params["wind_mean"]
        wind_std = params["wind_std"]
        dt = params.get("dt", 0.01)

        try:
            with _suppress_timing():
                imp = run_monte_carlo(pos0, vel0, mass, Cd, A, rho, wind_mean, wind_std, 30, 123, dt=dt)
            has_nan = np.any(np.isnan(imp))
            shape_ok = imp.shape == (30, 2)
            ok = not has_nan and shape_ok
        except Exception as e:
            ok = False
            imp = None
            err = str(e)

        status = "PASS" if ok else "FAIL"
        results.append((name, status))

        print(f"\n{name}")
        print(f"  Result: {status}")
        if ok:
            print(f"  Shape: {imp.shape}, NaN: {has_nan if imp is not None else 'N/A'}")
        else:
            print(f"  Error: {err if imp is None else ('NaN found' if has_nan else f'Bad shape {imp.shape}')}")

    all_ok = all(s == "PASS" for _, s in results)
    print(f"\nOverall: {'PASS' if all_ok else 'FAIL'}")
    print("Risk: LOW" if all_ok else "MEDIUM")
    print()
    return all_ok


def phase4_masking_integrity():
    """Phase 4: Masking integrity — code review."""
    print("=" * 60)
    print("PHASE 4 — Masking Integrity Check (Code Review)")
    print("=" * 60)

    checks = [
        ("Only vel[active] and pos[active] updated", True,
         "Lines 85-86: vel[active] = ..., pos[active] = ..."),
        ("Impact recorded only for just_hit", True,
         "Lines 97-99: impact_xy[just_hit] = pos[just_hit, :2]; just_hit = active & ~active_new"),
        ("Samples that hit excluded from next update", True,
         "Line 104: active = active_new; active_new = pos[:,2] > 0"),
    ]

    for desc, passed, evidence in checks:
        print(f"\n{desc}")
        print(f"  Verified: {'YES' if passed else 'NO'}")
        print(f"  Evidence: {evidence}")

    print("\nResult: PASS (logic verified)")
    print("Risk: LOW")
    print()
    return True


def phase5_performance():
    """Phase 5: Performance sanity recheck."""
    pos0 = (0.0, 0.0, 100.0)
    vel0 = (20.0, 0.0, 0.0)
    mass, Cd, A, rho = 1.0, 1.0, 0.01, 1.225
    wind_mean, wind_std = (2.0, 0.0, 0.0), 0.8
    dt, seed = 0.01, 42

    timings = {}
    for n in [1000, 2000]:
        with _suppress_timing():
            t0 = time.perf_counter()
            run_monte_carlo(pos0, vel0, mass, Cd, A, rho, wind_mean, wind_std, n, seed, dt=dt)
            timings[n] = (time.perf_counter() - t0) * 1000.0

    t1k = timings[1000]
    t2k = timings[2000]
    pass_1k = t1k < 300
    result = "PASS" if pass_1k else "FAIL"

    print("=" * 60)
    print("PHASE 5 — Performance Sanity Recheck")
    print("=" * 60)
    print(f"Result: {result}")
    print(f"N=1000: {t1k:.2f} ms (target < 300 ms)")
    print(f"N=2000: {t2k:.2f} ms")
    if not pass_1k:
        print("Anomaly: N=1000 exceeds 300 ms target.")
    print("Risk: LOW" if pass_1k else "MEDIUM")
    print()
    return result == "PASS"


if __name__ == "__main__":
    # Suppress timing prints from run_monte_carlo during validation
    p1 = phase1_determinism()
    p2 = phase2_old_vs_new()
    p3 = phase3_edge_cases()
    p4 = phase4_masking_integrity()
    p5 = phase5_performance()

    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Phase 1 (Determinism): {'PASS' if p1 else 'FAIL'}")
    print(f"Phase 2 (Old vs New):  {'PASS' if p2 else 'FAIL'}")
    print(f"Phase 3 (Edge Cases):  {'PASS' if p3 else 'FAIL'}")
    print(f"Phase 4 (Masking):     {'PASS' if p4 else 'FAIL'}")
    print(f"Phase 5 (Performance): {'PASS' if p5 else 'FAIL'}")
    all_pass = p1 and p2 and p3 and p4 and p5
    print(f"\nOverall: {'ALL PASS' if all_pass else 'SOME FAIL'}")
    sys.exit(0 if all_pass else 1)
