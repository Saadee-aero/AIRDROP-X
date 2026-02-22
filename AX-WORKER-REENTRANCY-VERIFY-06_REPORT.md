# AX-WORKER-REENTRANCY-VERIFY-06 Report
## SimulationWorker Concurrent Execution Verification

**Date:** 2025-02-22

---

## STEP 1: Re-entrancy Guard in _start_simulation()

**Location:** `qt_app/main_window.py` lines 1492-1494

```python
def _start_simulation(self, trigger: str) -> None:
    if self.simulation_running:
        return
```

**Mechanism:** `self.simulation_running` — boolean execution lock

- **Set True:** Line 1500, immediately after the guard, before `worker.start()`
- **Set False:** Line 1582, in `_on_simulation_finished()` when the QThread emits `finished`

**Conclusion:** There is a re-entrancy guard. A new worker cannot start while `simulation_running` is True.

---

## STEP 2: Worker Object Lifecycle

**Assignment:** Line 1509 — `self._simulation_worker = worker` (overwrites any previous reference)

**Clear:** Lines 1584-1586 in `_on_simulation_finished()`:
```python
if self._simulation_worker is not None:
    self._simulation_worker.deleteLater()
    self._simulation_worker = None
```

**Order of operations:**
1. Guard prevents starting if `simulation_running` is True
2. `simulation_running` only becomes False when `_on_simulation_finished` runs
3. `_on_simulation_finished` runs when the worker’s QThread emits `finished`
4. Before that, `_on_simulation_done` or `_on_simulation_failed` runs (from `simulation_done` / `simulation_failed`)

**Conclusion:** `_simulation_worker` is only replaced when starting a new worker, which can only happen after the previous worker has finished and `simulation_running` has been set False. Multiple workers cannot overlap.

---

## STEP 3: LIVE Timer Path

**Timer setup:** Line 141-142
```python
self.auto_timer = QTimer(self)
self.auto_timer.timeout.connect(self.auto_evaluate)
```

**auto_evaluate():** Lines 1457-1467
```python
def auto_evaluate(self) -> None:
    if self.system_mode != "LIVE":
        return
    if self.auto_evaluate_paused:
        return
    if not self.snapshot_active:
        return
    if self.simulation_running:   # <-- Guard
        return
    self._update_simulation_age()
    self._start_simulation(trigger="auto")
```

**Conclusion:** The timer timeout calls `auto_evaluate()`, which then calls `_start_simulation()`. There are two guards:
1. In `auto_evaluate`: `if self.simulation_running: return`
2. In `_start_simulation`: `if self.simulation_running: return`

Both prevent starting a new simulation while one is running.

---

## STEP 4: Summary

| Question | Answer |
|----------|--------|
| **Is there a re-entrancy guard?** | Yes |
| **What prevents concurrent workers?** | `self.simulation_running` — set True at start, False only in `_on_simulation_finished` |
| **Could multiple workers overlap?** | No — a new worker can only start after the previous one has finished and cleared the flag |
| **Is snapshot replacement order guaranteed?** | Yes — only one worker runs at a time; `_on_simulation_done` or `_on_simulation_failed` is the only path that updates `_latest_snapshot` from a worker |

---

## Callers of _start_simulation()

| Caller | Guard |
|--------|-------|
| `auto_evaluate()` (timer) | `simulation_running` checked before call |
| `_on_evaluate_clicked()` | `simulation_running` checked, shows "already running" message |
| `eventFilter` (READY block click) | `not self.simulation_running` in condition |

All callers rely on the same `simulation_running` flag, and `_start_simulation` re-checks it.
