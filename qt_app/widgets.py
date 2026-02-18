"""Reusable Qt widgets for AIRDROP-X Phase 1 shell."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget


class LeftPanelPlaceholder(QFrame):
    """Mission configuration panel placeholder."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("leftPanel")
        self.setFixedWidth(300)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        title = QLabel("MISSION CONFIGURATION", self)
        title.setObjectName("panelTitle")
        layout.addWidget(title)

        subtitle = QLabel("Desktop configuration panel", self)
        subtitle.setObjectName("panelSubtitle")
        layout.addWidget(subtitle)

        for text in (
            "Payload",
            "UAV State",
            "Target",
            "Environment",
            "Simulation",
            "Decision Threshold",
        ):
            label = QLabel(f"- {text}", self)
            label.setObjectName("placeholderLine")
            layout.addWidget(label)

        layout.addStretch(1)


class PlotAreaPlaceholder(QFrame):
    """Center plot area placeholder (FigureCanvasQTAgg will go here later)."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("plotPlaceholder")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)

        label = QLabel("PLOT CANVAS PLACEHOLDER", self)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setObjectName("plotPlaceholderText")
        layout.addWidget(label)


class StatusStrip(QFrame):
    """Bottom status placeholder row."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("statusStrip")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(2)

        self.snapshot_label = QLabel("Snapshot ID: --", self)
        self.snapshot_label.setObjectName("statusLabel")
        layout.addWidget(self.snapshot_label)

        self.telemetry_label = QLabel("Telemetry: Placeholder", self)
        self.telemetry_label.setObjectName("statusLabel")
        layout.addWidget(self.telemetry_label)
