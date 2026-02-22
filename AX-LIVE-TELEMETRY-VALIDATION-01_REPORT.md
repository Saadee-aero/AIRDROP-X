# AX-LIVE-TELEMETRY-VALIDATION-01 Report
## Snapshot Integrity and State Consistency During Live Telemetry Mode

**Date:** 2025-02-22  
**Scope:** Instrumentation only. No fixes applied.

---

## Instrumentation Added

**Location:** `qt_app/main_window.py` → `_handle_evaluation_result()` (immediately after `self._latest_snapshot = snapshot`)

**Prints added:**
- `SNAPSHOT ID:` (Python object id)
- `SNAPSHOT TYPE:` (from assigned snapshot)
- `LIVE SNAPSHOT TYPE:` (from local snapshot variable)
- `DECISION:`
- `P_HIT:`
- `hits:`
- `ci_low:`
- `ci_high:`
- `n_samples:`
- `SNAPSHOT HASH:`

---

## 1. Snapshot Replacement Behavior

**Code analysis:** `_handle_evaluation_result()` (lines 1633–1655)

- A new `snapshot` dict is built each cycle from `data` (lines 1633–1654).
- Assignment: `self._latest_snapshot = snapshot` (line 1655).
- No in-place mutation of the previous snapshot.
- Each cycle creates a new dict object and assigns it.

**Conclusion (code-based):** Snapshot is replaced, not mutated. `id(self._latest_snapshot)` should change every telemetry cycle.

**Runtime verification:** Run app in LIVE mode with telemetry active for 10+ cycles. Check that SNAPSHOT ID changes every cycle. If it stays constant, that indicates a bug.

---

## 2. Snapshot Type Stability

**Code analysis:**

- EvaluationWorker emits `snapshot_type: "EVALUATION"` in its result packet (evaluation_worker.py line 127).
- `_handle_evaluation_result` uses `data.get("snapshot_type", "EVALUATION")` when building the snapshot.
- In LIVE mode, only `_handle_evaluation_result` updates `_latest_snapshot`.
- No CONFIG snapshot is emitted during live evaluation; CONFIG is set only by:
  - `_on_mission_config_committed`
  - `_on_new_simulation_clicked`
  - `_seed_config_state`
  (none run during live evaluation)

**Conclusion (code-based):** During live telemetry, `snapshot_type` should always be `"EVALUATION"`.

**Runtime verification:** Ensure `LIVE SNAPSHOT TYPE:` prints `EVALUATION` every cycle. If `CONFIG` appears, there is a logic error.

---

## 3. Field Update Coherence

**Code analysis:**

All stat fields are populated from the same `data` packet in a single block:
- `hits`, `P_hit`, `ci_low`, `ci_high`, `n_samples` (plus `cep50`, `decision`, etc.) come from the same `data` dict.
- They are written into one new `snapshot` dict.
- Assignment to `_latest_snapshot` is atomic.

**Conclusion (code-based):** Updates should be coherent; no partial-update pattern.

**Runtime verification:** Inspect the printed `hits`, `P_hIT`, `ci_low`, `ci_high`, `n_samples` across cycles. They should move together (e.g. all change in the same cycle). If one lags or stays stale while others change, that suggests a coherence bug.

---

## 4. Decision Stability Behavior

**Code analysis:**

- `decision` is taken from `data.get("decision")` and stored in the new snapshot.
- `_render_mission_tab_operator()` is called with that `decision` and the new `snapshot`.
- In LIVE mode, `paused_info` is `None` when `_handle_evaluation_result` runs.
- `app_state` is set to `EVALUATED` before render.
- `_render_mission_tab` is not used in this path; only `_render_mission_tab_operator` is called.

**Conclusion (code-based):** Decision should be driven solely by the current evaluation and should not show READY unless evaluation says so.

**Runtime verification:** During live telemetry, observe the decision block:
- **Flicker:** Could happen if worker emits at high rate and UI update is slow.
- **Lag:** Possible if evaluation frequency (~5–7 Hz) does not match display refresh.
- **READY unexpectedly:** Would indicate `decision` being overridden or a wrong branch in render logic.

---

## 5. Hash Consistency Check

**Instrumentation:** `print("SNAPSHOT HASH:", hash(str(self._latest_snapshot)))`

**Conclusion (code-based):** Because each snapshot is a new dict built from new `data`, the string representation and therefore the hash should change every cycle when telemetry and Monte Carlo results change.

**Runtime verification:** Check that SNAPSHOT HASH changes most cycles (or every cycle if input/output changes). If the hash is constant for many cycles while telemetry is varying, that suggests stale or shared snapshots.

---

## Anomalies (Code Analysis)

- No clear anomalies from static inspection.
- One nuance: `impact_points` in the snapshot is a direct reference to `data.get("impact_points", [])`. If the worker reuses or mutates the same list across emissions, that could cause shared-state issues. The EvaluationWorker constructs its packet with `impact_points` from the adapter result; adapter returns new arrays. So in normal operation this should be safe.

**To fully validate:** Run the app in LIVE mode with telemetry for 10+ cycles and collect the instrumentation output for review.
