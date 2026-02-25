"""
AX-UNCERTAINTY-DECOMPOSITION-21: Uncertainty contribution decomposition.
Normalize sensitivity gradients to relative contribution weights.
AX-UNCERTAINTY-HARDEN-24: Divide-by-zero guard, dominance stability.
"""

from __future__ import annotations

from typing import Any


def compute_uncertainty_contribution(snapshot: dict[str, Any]) -> None:
    """
    AX-UNCERTAINTY-DECOMPOSITION-21: Add uncertainty_contribution to snapshot (mutates in place).

    Requires sensitivity_matrix. No-op if not present.
    """
    sens = snapshot.get("sensitivity_matrix")
    if not sens or not isinstance(sens, dict):
        return

    wind = abs(float(sens.get("wind", 0) or 0))
    altitude = abs(float(sens.get("altitude", 0) or 0))
    velocity = abs(float(sens.get("velocity", 0) or 0))

    total = wind + altitude + velocity
    if total < 1e-6:
        snapshot["uncertainty_contribution"] = {
            "wind": 1.0 / 3.0,
            "altitude": 1.0 / 3.0,
            "velocity": 1.0 / 3.0,
        }
        return

    weights = {
        "wind": wind / total,
        "altitude": altitude / total,
        "velocity": velocity / total,
    }
    snapshot["uncertainty_contribution"] = weights

    ranked = sorted(
        [("wind", weights["wind"]), ("altitude", weights["altitude"]), ("velocity", weights["velocity"])],
        key=lambda x: -x[1],
    )
    if len(ranked) >= 2 and ranked[0][1] < ranked[1][1] + 0.05:
        snapshot["dominant_risk_factor"] = "Mixed"
