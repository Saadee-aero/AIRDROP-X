# AX-HYSTERESIS-ERROR-TRANSITION-VERIFY-05 Report
## Hysteresis Behavior Across EVALUATION → ERROR → EVALUATION

**Date:** 2025-02-22

---

## STEP 1: Source of previous_decision

**Locations:**
- `qt_app/main_window.py` line ~1516: `_on_simulation_done()`
- `qt_app/main_window.py` line ~1716: `_handle_evaluation_result()`

**Code pattern:**
```python
last_snapshot = self._latest_snapshot or {}
previous_decision = last_snapshot.get("decision") if last_snapshot.get("snapshot_type") == "EVALUATION" else None
```

**Equivalent logic:**
```python
if last_snapshot.get("snapshot_type") == "EVALUATION":
    previous_decision = last_snapshot.get("decision")
else:
    previous_decision = None
```

**Confirmed:** The pattern matches the intended behavior. `previous_decision` is derived only from the previous snapshot when its type is `"EVALUATION"`; otherwise it is `None`.

---

## STEP 2: Behavior Across ERROR Transition

**Sequence:**
- **Snapshot A** = EVALUATION (decision="DROP") → `_latest_snapshot` = A
- **Snapshot B** = ERROR → `_latest_snapshot` = B (snapshot_type="ERROR")
- **Snapshot C** = new EVALUATION → processing C

**When processing Snapshot C:**
- `last_snapshot` = `self._latest_snapshot` = B (ERROR snapshot)
- `last_snapshot.get("snapshot_type")` = `"ERROR"`
- `last_snapshot.get("snapshot_type") == "EVALUATION"` → **False**
- `previous_decision` = **None**

**Conclusion:** For Snapshot C, `previous_decision == None`, not `"DROP"`. Hysteresis memory resets correctly across the ERROR transition.

---

## STEP 3: Debug Print

**Location:** `src/decision_stability.py`, inside `enrich_evaluation_snapshot()`:

```python
print("PREVIOUS DECISION USED:", previous_decision)  # AX-HYSTERESIS-ERROR-TRANSITION-VERIFY-05
```

**How to verify:**
1. Run manual evaluation → expect `PREVIOUS DECISION USED: None` (no prior EVALUATION).
2. Force worker error (e.g. adapter failure) → ERROR snapshot shown; no call to `enrich_evaluation_snapshot`.
3. Run evaluation again → expect `PREVIOUS DECISION USED: None` (last snapshot was ERROR).

---

## Summary

| Transition          | last_snapshot type | previous_decision |
|---------------------|--------------------|-------------------|
| EVALUATION → EVALUATION | EVALUATION         | From prior decision |
| EVALUATION → ERROR      | —                  | No enrichment call  |
| ERROR → EVALUATION      | ERROR              | **None**            |

**Hysteresis memory resets correctly:** After an ERROR snapshot, the next EVALUATION snapshot is treated as having no prior decision, so hysteresis uses the raw threshold rule instead of carrying over the previous DROP/NO DROP state.
