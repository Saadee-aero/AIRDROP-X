# AX-SENSITIVITY-STABILITY-AUDIT-10 Report

**Sensitivity Layer Stability & Execution Safety Audit**

---

## STEP 1 — Gradient Variability

### Debug Instrumentation Added

In `src/sensitivity.py` (LIVE mode branch):
```python
print("P_base:", P_base)
print("P_perturbed:", P_perturbed)
print("dP_dW:", dP_dW)
```

### How to Run 20 LIVE Cycles

1. Start app, configure payload, commit.
2. Switch system mode to LIVE (or use LIVE execution).
3. Enable LIVE from the Execution panel.
4. Observe console for 20 cycles of:
   - `P_base: <value>`
   - `P_perturbed: <value>`
   - `dP_dW: <value>`

### Expected Behavior (Code Inspection)

- **Gradient sign:** `dP_dW = (P_perturbed - P_base) / 0.5`. With wind_x +0.5 m/s, P_perturbed will typically differ from P_base. Sign depends on geometry and dispersion; positive wind usually shifts impact downwind.
- **Monte Carlo variance:** LIVE uses `n_samples = max(30, int(n_orig * 0.3))` for the perturbed run. Small sample counts increase variance.
- **Classification:** `_wind_sensitivity_level(dP_dW)` uses thresholds: |dP_dW| ≥ 0.05 → High; ≥ 0.02 → Moderate; else Low. Near thresholds, classification can switch between cycles.

### Verification Checklist

- [ ] Run LIVE for 20 cycles and record P_base, P_perturbed, dP_dW.
- [ ] Does gradient sign flip frequently? (indicates high variance or regime changes)
- [ ] Does classification (High/Moderate/Low) oscillate rapidly? (check near 0.02 or 0.05)

---

## STEP 2 — Performance Check

### Instrumentation Added

- **SimulationWorker path:** `main_window._on_simulation_done` prints `compute_time_ms`.
- **EvaluationWorker path (LIVE):** Prints `eval_cycle_ms` (full cycle including base + perturbed run).

### Timer Intervals

- `_live_timer` interval: **200 ms**
- EvaluationWorker `target_period`: **0.15 s (150 ms)**

### Verification

- **SimulationWorker:** `compute_time_ms` covers base evaluation + LIVE/ANALYTICAL sensitivity (1 or 3 extra runs). For LIVE, total ≈ 2× base eval time. Should be **< 200 ms** if base eval is ~50–80 ms.
- **EvaluationWorker:** `eval_cycle_ms` should be **< 150 ms** to keep loop rate; if it exceeds 150 ms, `sleep_time` becomes 0 and effective rate drops.

### Risk

- ANALYTICAL mode (3 perturbed runs) can push `compute_time_ms` above 200 ms for heavier configs.
- LIVE with sensitivity adds ~1× base eval time; marginal but acceptable if base is fast.

---

## STEP 3 — Worker Flow

### Execution Path (Code Verified)

**SimulationWorker (Run Once, LIVE button, manual_lock):**
1. `_start_simulation()` creates single SimulationWorker with `cfg`.
2. Worker `run()` calls `run_simulation_snapshot(config_override=cfg)`.
3. Adapter runs base eval, then `compute_sensitivity(result, overrides, mode)` **before** `return result`.
4. Worker sets `snapshot["compute_time_ms"]`, emits `simulation_done`.
5. No extra workers; all work done in the same worker thread.

**EvaluationWorker (LIVE telemetry):**
1. Loop: `override["sensitivity_mode"] = "LIVE"` → `run_simulation_snapshot(override)`.
2. Adapter runs base eval, then `compute_sensitivity(result, override, "LIVE")` **before** return.
3. Worker builds `emit_data`, includes `sensitivity_live`, emits `result_ready`.
4. Single EvaluationWorker thread; no additional workers.

### Confirmation

- Sensitivity computation completes inside `run_simulation_snapshot` before the function returns.
- Snapshot is emitted only after the full adapter call (including sensitivity).
- No extra workers; perturbations run synchronously via `_run_perturbed()` → `run_simulation_snapshot()` in the same thread.

---

## STEP 4 — Mode Isolation

### LIVE Mode

- `sensitivity_mode = "LIVE"` passed from:
  - `main_window._start_simulation`: `cfg["sensitivity_mode"] = "LIVE"` when `system_mode == "LIVE"`
  - `evaluation_worker`: `override["sensitivity_mode"] = "LIVE"`

- `compute_sensitivity(..., "LIVE")` only fills `snapshot["sensitivity_live"]`.
- Does **not** compute `sensitivity_matrix` or `dominant_risk_factor` (only in ANALYTICAL branch).

### ANALYTICAL Mode

- `sensitivity_mode = "ANALYTICAL"` passed from `main_window._start_simulation` when `system_mode != "LIVE"`.
- `compute_sensitivity(..., "ANALYTICAL")` fills `sensitivity_matrix` and `dominant_risk_factor`.
- Does **not** compute `sensitivity_live` (only in LIVE branch).

### Perturbed Runs

- `_run_perturbed()` does `cfg.pop("sensitivity_mode", None)` before calling `run_simulation_snapshot`.
- Perturbed runs therefore have no `sensitivity_mode` in overrides.
- Adapter: `if sensitivity_mode in ("LIVE", "ANALYTICAL"):` → false when `sensitivity_mode` is absent → no sensitivity computation.
- Perturbed runs do **not** run sensitivity.

---

## Summary

| Check                | Status                                      |
|----------------------|---------------------------------------------|
| Gradient stability   | Requires live run; debug prints added       |
| Performance margin   | Logging added; verify compute_time_ms < 200 |
| Worker safety        | Confirmed: single worker, synchronous flow  |
| Mode isolation       | Confirmed: LIVE vs ANALYTICAL, no recursion |

---

## Removing Audit Instrumentation

After the audit, remove:
1. `src/sensitivity.py`: the three `print` calls in the LIVE branch
2. `qt_app/main_window.py`: the `print("compute_time_ms:", ...)` line
3. `qt_app/evaluation_worker.py`: the `print("eval_cycle_ms:", ...)` line
