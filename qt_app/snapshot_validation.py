"""
Snapshot validation and observability. AX-OBSERVABILITY-03.
"""
from __future__ import annotations

_REQUIRED_EVALUATION_KEYS = frozenset({
    "snapshot_type", "decision", "P_hit", "ci_low", "ci_high", "n_samples",
})
_REQUIRED_CONFIG_KEYS = frozenset({"snapshot_type", "threshold_pct"})
_REQUIRED_ERROR_KEYS = frozenset({"snapshot_type", "error_message"})


def validate_snapshot(snapshot: dict | None) -> None:
    """
    Raise descriptive error if required keys are missing.
    CONFIG and ERROR types have minimal requirements.
    """
    if snapshot is None:
        raise ValueError("Snapshot is None")
    st = snapshot.get("snapshot_type")
    if st == "CONFIG":
        missing = _REQUIRED_CONFIG_KEYS - set(snapshot)
        if missing:
            raise ValueError(f"CONFIG snapshot missing keys: {missing}")
    elif st == "ERROR":
        missing = _REQUIRED_ERROR_KEYS - set(snapshot)
        if missing:
            raise ValueError(f"ERROR snapshot missing keys: {missing}")
    elif st == "EVALUATION":
        missing = _REQUIRED_EVALUATION_KEYS - set(snapshot)
        if missing:
            raise ValueError(f"EVALUATION snapshot missing keys: {missing}")
    else:
        raise ValueError(f"Invalid snapshot_type: {st!r}")
