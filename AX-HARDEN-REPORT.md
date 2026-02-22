# AX-HYSTERESIS-HARDEN-01, AX-STABILITY-CLAMP-02, AX-ERROR-STATE-HARDEN-03
## Implementation Report

**Date:** 2025-02-22

---

## AX-HYSTERESIS-HARDEN-01

### Hysteresis memory source

**Source:** Previous snapshot only. No global variables, UI state, or app_state.

```python
previous_decision = last_snapshot.get("decision") if last_snapshot.get("snapshot_type") == "EVALUATION" else None
```

**Where set:** In `_on_simulation_done()` and `_handle_evaluation_result()` immediately before enrichment:

- `last_snapshot = self._latest_snapshot or {}`
- `previous_decision = last_snapshot.get("decision") if last_snapshot.get("snapshot_type") == "EVALUATION" else None`

### Function signature

`enrich_evaluation_snapshot(snapshot: dict, previous_decision: str | None) -> dict`

- `previous_decision` is passed explicitly.
- Uses only snapshot history; no `system_mode`, paused flags, or UI memory.

### Changes

- Removed `self._last_decision`.
- Removed `self._last_decision = None` from New Simulation.
- Callers derive `previous_decision` from `self._latest_snapshot` before assigning a new snapshot.

---

## AX-STABILITY-CLAMP-02

### Updates in `src/decision_stability.py`

1. **EPSILON**
   - Replaced `_SMALL` with `EPSILON = 1e-6`.

2. **`stability_index` clamping**
   - `stability_index = min(si, 100.0)` to cap at 100.0.

3. **Numerical limit handling**
   - If `ci_width < EPSILON`, set `snapshot["robustness_status"] = "NUMERICAL_LIMIT"`.
   - Otherwise, use the usual robustness computation (ROBUST / FRAGILE / UNSAFE).

---

## AX-ERROR-STATE-HARDEN-03

### ERROR state UI behavior

When `snapshot_type == "ERROR"`:

1. **Decision block**
   - Shows "SYSTEM ERROR".
   - Error message in paused_message_label.

2. **Stats panel**
   - HIT %, HITS, Stability, Sample count, CEP50, 95% CI, CI width set to empty labels.

3. **Impact cloud**
   - `mission_fig_op.clear()` plus a blank subplot.

4. **Advisory**
   - Reason, Statistical note, Actions set to "—".

5. **Current factors**
   - Wind, Altitude, Speed set to "—".

6. **Analysis tab**
   - `_render_analysis_tab()` called so impact cloud uses empty data.

### Render order

- `_render_mission_tab_operator_error()` runs first and clears all relevant widgets.
- Then `_render_analysis_tab()` clears the analysis impact cloud.
- No prior P_hit or decision values remain visible.
