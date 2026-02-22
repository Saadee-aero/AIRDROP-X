# AX-DECISION-BLOCK-STATE-ALIGNMENT-01 Report
## Decision Block Rendering Logic Aligned with Snapshot Authority

**Date:** 2025-02-22

---

## 1. Previous Authority Variables Removed

**EVALUATION path (removed):**
- `paused_info` — no longer overrides decision for EVALUATION snapshots
- `app_state == AppState.EVALUATED` — no longer gates use of snapshot decision
- `impact_points` check — no longer required before using snapshot decision

**CONFIG path (retained for READY/PAUSED):**
- `paused_info` from `_get_paused_reason()` — still used for CONFIG only to show operational blockers ("Configure Payload", "Computing — Standby", "Calibrate Telemetry"). CONFIG snapshot has no decision field; operational state drives READY vs PAUSED.

---

## 2. Decision Block Now Snapshot-Driven

**EVALUATION snapshots:**
- `decision = snapshot.get("decision")` — sole source
- Fallback: threshold-based DROP/NO DROP if value missing or invalid
- Advisory override: if `advisory` present, may override from `current_feasibility`
- `paused_info = None` — no external pause override

**CONFIG snapshots:**
- `decision = "PAUSED"` if `paused_info` else `"READY"`
- `paused_info` comes from `_get_paused_reason()` (operational blockers only)

**Prints added:**
- `DECISION BLOCK STATE SOURCE: paused_info` (CONFIG path)
- `SNAPSHOT TYPE:`, `SNAPSHOT DECISION:` (inside `_render_mission_tab_operator`)

---

## 3. Stats Panels Now Snapshot-Driven

**Change:** Stats panel gating updated from `decision_upper in ("DROP", "NO DROP")` to `snapshot_type == "EVALUATION"`.

**Effect:**
- Stats render whenever `snapshot["snapshot_type"] == "EVALUATION"`
- No dependency on `system_mode`, `paused` flag, or `decision`
- CONFIG snapshots: empty stat labels
- EVALUATION snapshots: full stats (HIT %, HITS, Stability, 95% CI, CI width, Sample count, CEP50)

---

## Summary

| Path    | Decision source                     | Stats source             |
|---------|-------------------------------------|--------------------------|
| CONFIG  | paused_info (operational blockers)  | Hidden (config_only)     |
| EVALUATION | snapshot["decision"]             | snapshot_type == EVALUATION |

No architecture refactor. No evaluation worker changes. No snapshot schema changes.
