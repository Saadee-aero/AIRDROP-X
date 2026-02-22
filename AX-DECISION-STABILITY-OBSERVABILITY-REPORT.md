# AX-DECISION-STABILITY-01, AX-SNAPSHOT-AUTHORITY-02, AX-OBSERVABILITY-03
## Implementation Report

**Date:** 2025-02-22

---

## AX-DECISION-STABILITY-01

### Hysteresis Implementation

**Location:** `src/decision_stability.py` — `apply_decision_hysteresis()`, `enrich_evaluation_snapshot()`

**Constant:** `HYSTERESIS_MARGIN_PCT = 1.0`

**Logic:**
- Previous DROP: keep DROP unless P_hit < threshold − 1%
- Previous NO DROP: keep NO DROP unless P_hit > threshold + 1%
- No previous: use raw threshold rule

**Integration:** `enrich_evaluation_snapshot()` is called from:
- `_on_simulation_done()` (one-shot simulation)
- `_handle_evaluation_result()` (LIVE evaluation worker)

**State:** `_last_decision` on MainWindow; reset on New Simulation.

### Robustness Logic

**Location:** `src/decision_stability.py` — `compute_robustness_status()`

| Condition | robustness_status |
|-----------|-------------------|
| ci_lower > threshold | ROBUST |
| ci_lower ≤ threshold ≤ ci_upper | FRAGILE |
| ci_upper < threshold | UNSAFE |

### New Snapshot Fields

| Field | Description |
|-------|-------------|
| `robustness_status` | ROBUST / FRAGILE / UNSAFE / UNKNOWN |
| `stability_index` | distance_from_threshold / max(ci_width, ε) |
| `compute_time_ms` | Evaluation compute time (SimulationWorker) |
| `render_time_ms` | UI render time (main thread) |

### UI Update

**Location:** `_render_mission_tab_operator()` — decision label

**Display:** DROP/NO DROP with robustness tag appended, e.g.:
- `DROP (ROBUST)`
- `NO DROP (FRAGILE)`
- `DROP (UNSAFE)`

---

## AX-SNAPSHOT-AUTHORITY-02

### Advisory Panel

**Sources:** All from snapshot:
- `snapshot["decision"]` (via decision param)
- `snapshot["decision_reason"]`
- `snapshot["doctrine_description"]`
- `snapshot["P_hit"]`, `snapshot["ci_low"]`, `snapshot["ci_high"]` (stats panels)
- `snapshot["advisory"]` when present

No direct use of worker objects, live flags, or paused flags.

### Decision Block

**Sources:**
- `snapshot["snapshot_type"]`
- `snapshot["decision"]`
- `snapshot["robustness_status"]`

### CONFIG Path

CONFIG still uses `_get_paused_reason()` (app_state, simulation_running, system_mode) for READY vs PAUSED. Snapshot does not store these; they remain operational state.

EVALUATION and ERROR paths are fully snapshot-driven.

---

## AX-OBSERVABILITY-03

### Snapshot Validation

**Location:** `qt_app/snapshot_validation.py` — `validate_snapshot(snapshot)`

**Required keys:**
- CONFIG: `snapshot_type`, `threshold_pct`
- EVALUATION: `snapshot_type`, `decision`, `P_hit`, `ci_low`, `ci_high`, `n_samples`
- ERROR: `snapshot_type`, `error_message`

**Usage:** Called in `_render_mission_tab()` before render. On validation failure, switches to ERROR snapshot.

### State Transition Logging

**Location:** `_log_state_transition(new_type)` in main_window.py

**Format:** `STATE TRANSITION: <old> → <new>`

Invoked when snapshot type changes (CONFIG, EVALUATION, ERROR).

### Performance Metrics

| Metric | Where Set |
|--------|-----------|
| `compute_time_ms` | SimulationWorker.run() |
| `render_time_ms` | _on_simulation_done(), _handle_evaluation_result() |

### ERROR Snapshot Type

**Format:**
```python
{"snapshot_type": "ERROR", "error_message": str(exception)}
```

**Use:** SimulationWorker failure → `_on_simulation_failed()` → ERROR snapshot → `_render_mission_tab_operator_error()`.

**Display:** Decision block shows "SYSTEM ERROR" with error message.

---

## Files Modified / Added

| File | Changes |
|------|---------|
| `src/decision_stability.py` | New: hysteresis, robustness, stability_index |
| `qt_app/snapshot_validation.py` | New: validate_snapshot() |
| `qt_app/main_window.py` | Enrichment, validation, ERROR handling, robustness UI, transition logging, metrics |
