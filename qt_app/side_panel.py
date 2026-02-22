"""Left mission configuration panel for Qt app."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from widgets import NoWheelDoubleSpinBox, NoWheelSpinBox


class MissionConfigPanel(QWidget):
    """Mission configuration input panel for desktop parity."""

    telemetry_source_apply_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("leftPanel")
        self.setFixedWidth(300)
        self._snapshot_locked = False
        self._system_mode = "SNAPSHOT"
        self._build_ui()
        self._load_defaults()
        self.apply_state(self._system_mode, self._snapshot_locked)

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(14)

        # Group 0: SYSTEM MODE
        mode_group, mode_form = self._make_group("System mode")
        self.system_mode_combo = QComboBox(self)
        self.system_mode_combo.addItem("Snapshot", "SNAPSHOT")
        self.system_mode_combo.addItem("Live telemetry", "LIVE")
        self.system_mode_combo.setCurrentIndex(0)
        mode_form.addRow("Mode", self.system_mode_combo)
        root.addWidget(mode_group)

        self.panel_title_label = QLabel("MISSION CONFIGURATION (Snapshot)", self)
        self.panel_title_label.setObjectName("panelTitle")
        root.addWidget(self.panel_title_label)

        self.panel_subtitle_label = QLabel("Parameters frozen at last evaluation.", self)
        self.panel_subtitle_label.setObjectName("panelSubtitle")
        root.addWidget(self.panel_subtitle_label)

        self.snapshot_meta_label = QLabel("Snapshot ID: ---", self)
        self.snapshot_meta_label.setObjectName("panelFieldValue")
        root.addWidget(self.snapshot_meta_label)

        # Group 1: PAYLOAD
        payload_group, payload_form = self._make_group("PAYLOAD")
        self.mass = self._double_spin(0.1, 1000.0, 0.1, 3)
        self.cd = self._double_spin(0.01, 10.0, 0.01, 3)
        self.area = self._double_spin(0.001, 10.0, 0.001, 4)
        self.payload_widgets = [self.mass, self.cd, self.area]
        payload_form.addRow("Mass (kg)", self.mass)
        payload_form.addRow("Drag Coefficient", self.cd)
        self.cd_assumption_label = QLabel("User-defined assumption", payload_group)
        self.cd_assumption_label.setObjectName("panelSubtitle")
        self.cd_assumption_label.setVisible(False)
        payload_form.addRow(self.cd_assumption_label)
        payload_form.addRow("Reference Area (m²)", self.area)
        self.cd.valueChanged.connect(self._refresh_cd_assumption_badge)
        root.addWidget(payload_group)

        # Group 2: UAV STATE
        uav_group, uav_form = self._make_group("UAV STATE")
        self.uav_mode_badge = QLabel("Live", uav_group)
        self.uav_mode_badge.setObjectName("panelSubtitle")
        uav_form.addRow(self.uav_mode_badge)
        self.uav_x = self._double_spin(-1_000_000.0, 1_000_000.0, 1.0, 2)
        self.uav_y = self._double_spin(-1_000_000.0, 1_000_000.0, 1.0, 2)
        self.uav_altitude = self._double_spin(10.0, 100_000.0, 10.0, 2)
        self.uav_vx = self._double_spin(-5000.0, 5000.0, 1.0, 2)
        self.uav_widgets = [self.uav_x, self.uav_y, self.uav_altitude, self.uav_vx]
        uav_form.addRow("UAV X (m)", self.uav_x)
        uav_form.addRow("UAV Y (m)", self.uav_y)
        uav_form.addRow("UAV Altitude (m)", self.uav_altitude)
        uav_form.addRow("UAV Velocity X (m/s)", self.uav_vx)
        root.addWidget(uav_group)

        # Group 3: TARGET
        target_group, target_form = self._make_group("TARGET")
        self.target_x = self._double_spin(-1_000_000.0, 1_000_000.0, 1.0, 2)
        self.target_y = self._double_spin(-1_000_000.0, 1_000_000.0, 1.0, 2)
        self.target_radius = self._double_spin(0.1, 100_000.0, 0.5, 2)
        self.target_widgets = [self.target_x, self.target_y, self.target_radius]
        target_form.addRow("Target X (m)", self.target_x)
        target_form.addRow("Target Y (m)", self.target_y)
        target_form.addRow("Target Radius (m)", self.target_radius)
        root.addWidget(target_group)

        # Group 4: ENVIRONMENT
        env_group, env_form = self._make_group("ENVIRONMENT")
        self.environment_badge = QLabel("Telemetry-driven", env_group)
        self.environment_badge.setObjectName("panelSubtitle")
        env_form.addRow(self.environment_badge)
        self.wind_x = self._double_spin(-500.0, 500.0, 0.5, 3)
        self.wind_std = self._double_spin(0.0, 500.0, 0.1, 3)
        self.environment_widgets = [self.wind_x, self.wind_std]
        env_form.addRow("Wind X (m/s)", self.wind_x)
        self.wind_std_label = QLabel("Wind Std Dev (m/s)", env_group)
        env_form.addRow(self.wind_std_label, self.wind_std)
        root.addWidget(env_group)

        # Group 5: SIMULATION
        sim_group, sim_form = self._make_group("SIMULATION")
        self.num_samples = NoWheelSpinBox(self)
        self.num_samples.setRange(50, 1000)
        self.num_samples.setSingleStep(50)
        self.random_seed = NoWheelSpinBox(self)
        self.random_seed.setRange(0, 2_147_483_647)
        self.random_seed.setSingleStep(1)
        self.simulation_widgets = [self.num_samples, self.random_seed]
        sim_form.addRow("Monte Carlo Samples", self.num_samples)
        sim_form.addRow("Random Seed", self.random_seed)
        root.addWidget(sim_group)

        # Group 5b: TELEMETRY SOURCE (LIVE) — Mock vs File playback
        self.telemetry_source_group, telemetry_source_form = self._make_group("TELEMETRY SOURCE")
        self.telemetry_source_combo = QComboBox(self)
        self.telemetry_source_combo.addItem("Mock", "mock")
        self.telemetry_source_combo.addItem("File playback", "file")
        self.telemetry_source_combo.setCurrentIndex(0)
        telemetry_source_form.addRow("Source", self.telemetry_source_combo)
        self.telemetry_file_path = QLineEdit(self)
        self.telemetry_file_path.setPlaceholderText("Path to CSV...")
        telemetry_source_form.addRow("File path", self.telemetry_file_path)
        browse_btn = QPushButton("Browse...", self.telemetry_source_group)
        browse_btn.clicked.connect(self._browse_telemetry_file)
        telemetry_source_form.addRow(browse_btn)
        self.telemetry_source_apply_btn = QPushButton("Apply", self.telemetry_source_group)
        self.telemetry_source_apply_btn.clicked.connect(self.telemetry_source_apply_requested.emit)
        telemetry_source_form.addRow(self.telemetry_source_apply_btn)
        root.addWidget(self.telemetry_source_group)

        # Group 6: TELEMETRY HEALTH (LIVE)
        self.telemetry_group, telemetry_form = self._make_group("TELEMETRY HEALTH")
        self.telemetry_health_label = QLabel(
            "Packet Rate: -- Hz | Last: -- s | Status: --",
            self.telemetry_group,
        )
        self.telemetry_health_label.setObjectName("panelFieldValue")
        self.sim_age_label = QLabel("Simulation Age: --", self.telemetry_group)
        self.sim_age_label.setObjectName("panelFieldValue")
        telemetry_form.addRow(self.telemetry_health_label)
        telemetry_form.addRow(self.sim_age_label)
        root.addWidget(self.telemetry_group)

        # Group 7: AUTO-EVALUATE (LIVE)
        self.auto_group, auto_form = self._make_group("AUTO-EVALUATE")
        self.auto_eval_combo = QComboBox(self)
        self.auto_eval_combo.addItems(["OFF", "1s", "2s"])
        auto_form.addRow("Auto-evaluate", self.auto_eval_combo)
        self.auto_pause_label = QLabel("Auto-evaluate paused (performance).", self.auto_group)
        self.auto_pause_label.setObjectName("panelSubtitle")
        self.auto_pause_label.setVisible(False)
        auto_form.addRow(self.auto_pause_label)
        root.addWidget(self.auto_group)

        # Group 8: DECISION THRESHOLD
        threshold_group, threshold_form = self._make_group("DECISION THRESHOLD")
        self.threshold_pct = self._double_spin(0.0, 100.0, 1.0, 0)
        self.threshold_widgets = [self.threshold_pct]
        threshold_form.addRow("Probability Threshold (%)", self.threshold_pct)
        root.addWidget(threshold_group)

        root.addStretch(1)

    def _make_group(self, title: str) -> tuple[QFrame, QFormLayout]:
        container = QFrame(self)
        container.setObjectName("configGroup")
        container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        vbox = QVBoxLayout(container)
        vbox.setContentsMargins(10, 10, 10, 10)
        vbox.setSpacing(10)
        label = QLabel(title, container)
        label.setObjectName("groupTitle")
        vbox.addWidget(label)
        form = QFormLayout()
        form.setHorizontalSpacing(12)
        form.setVerticalSpacing(8)
        vbox.addLayout(form)
        return container, form

    def _double_spin(self, minimum: float, maximum: float, step: float, decimals: int) -> NoWheelDoubleSpinBox:
        box = NoWheelDoubleSpinBox(self)
        box.setRange(minimum, maximum)
        box.setSingleStep(step)
        box.setDecimals(decimals)
        return box

    def _load_defaults(self) -> None:
        from configs import mission_configs as cfg

        self.mass.setValue(float(cfg.mass))
        self.cd.setValue(float(cfg.Cd))
        self.area.setValue(float(cfg.A))

        self.uav_x.setValue(float(cfg.uav_pos[0]))
        self.uav_y.setValue(float(cfg.uav_pos[1]))
        self.uav_altitude.setValue(float(cfg.uav_pos[2]))
        self.uav_vx.setValue(float(cfg.uav_vel[0]))

        self.target_x.setValue(float(cfg.target_pos[0]))
        self.target_y.setValue(float(cfg.target_pos[1]))
        self.target_radius.setValue(float(cfg.target_radius))

        self.wind_x.setValue(float(cfg.wind_mean[0]))
        self.wind_std.setValue(float(cfg.wind_std))

        self.num_samples.setValue(int(cfg.n_samples))
        self.random_seed.setValue(int(cfg.RANDOM_SEED))
        self.threshold_pct.setRange(float(cfg.THRESHOLD_SLIDER_MIN), float(cfg.THRESHOLD_SLIDER_MAX))
        self.threshold_pct.setValue(float(cfg.THRESHOLD_SLIDER_INIT))

    def _set_enabled(self, widgets: list[QWidget], enabled: bool) -> None:
        for widget in widgets:
            widget.setEnabled(enabled)

    def apply_state(self, system_mode: str, snapshot_locked: bool) -> None:
        mode = str(system_mode or "SNAPSHOT").strip().upper()
        if mode not in ("SNAPSHOT", "LIVE"):
            mode = "SNAPSHOT"
        self._system_mode = mode
        self._snapshot_locked = bool(snapshot_locked)
        idx = self.system_mode_combo.findData(mode)
        if idx < 0:
            idx = 0
        self.system_mode_combo.blockSignals(True)
        self.system_mode_combo.setCurrentIndex(idx)
        self.system_mode_combo.blockSignals(False)

        if mode == "LIVE":
            self.panel_title_label.setText("MISSION CONFIGURATION (Live Telemetry)")
            self.panel_subtitle_label.setText("UAV state from live telemetry. Payload assumptions fixed.")
            self.uav_mode_badge.setVisible(True)
            self.environment_badge.setVisible(True)
            self.wind_std_label.setText("Wind σ (m/s)")
        else:
            self.panel_title_label.setText("MISSION CONFIGURATION (Snapshot)")
            self.panel_subtitle_label.setText("Parameters frozen at last evaluation.")
            self.uav_mode_badge.setVisible(False)
            self.environment_badge.setVisible(False)
            self.wind_std_label.setText("Wind Std Dev (m/s)")

        # Streamlit behavior parity:
        # - Payload/Target/Simulation editable until snapshot lock.
        # - In LIVE, UAV + ENVIRONMENT are telemetry-driven (always read-only).
        lock = self._snapshot_locked
        self._set_enabled(self.payload_widgets, not lock)
        self._set_enabled(self.target_widgets, not lock)
        self._set_enabled(self.simulation_widgets, not lock)
        self._set_enabled(self.threshold_widgets, True)

        if mode == "LIVE":
            self._set_enabled(self.uav_widgets, False)
            self._set_enabled(self.environment_widgets, False)
            self.telemetry_source_group.setVisible(True)
            self.telemetry_group.setVisible(True)
            self.auto_group.setVisible(True)
        else:
            self._set_enabled(self.uav_widgets, not lock)
            self._set_enabled(self.environment_widgets, not lock)
            self.telemetry_source_group.setVisible(False)
            self.telemetry_group.setVisible(False)
            self.auto_group.setVisible(False)
            self.auto_pause_label.setVisible(False)
            self.auto_eval_combo.blockSignals(True)
            self.auto_eval_combo.setCurrentText("OFF")
            self.auto_eval_combo.blockSignals(False)

        self._refresh_cd_assumption_badge()

    def set_system_mode(self, mode: str) -> None:
        self.apply_state(mode, self._snapshot_locked)

    def system_mode(self) -> str:
        raw = self.system_mode_combo.currentData()
        if raw in ("SNAPSHOT", "LIVE"):
            return str(raw)
        return self._system_mode

    def set_read_only(self, state: bool) -> None:
        self.apply_state(self._system_mode, bool(state))

    def set_snapshot_id(self, snapshot_id: str) -> None:
        self.snapshot_meta_label.setText(f"Snapshot ID: {snapshot_id}")

    def set_telemetry_health(self, packet_rate_hz: float, age_s: float, status: str) -> None:
        self.telemetry_health_label.setText(
            f"Packet Rate: {packet_rate_hz:.1f} Hz | Last: {age_s:.2f} s | Status: {status}"
        )

    def set_simulation_age(self, age_s: float | None) -> None:
        if age_s is None:
            self.sim_age_label.setText("Simulation Age: --")
            return
        self.sim_age_label.setText(f"Simulation Age: {age_s:.1f}s")

    def set_auto_evaluate_paused(self, paused: bool) -> None:
        self.auto_pause_label.setVisible(bool(paused) and self._system_mode == "LIVE")

    def _refresh_cd_assumption_badge(self, *_args) -> None:
        show = (not self._snapshot_locked) and (abs(float(self.cd.value()) - 0.47) > 1e-9)
        self.cd_assumption_label.setVisible(show)

    def _browse_telemetry_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select telemetry CSV",
            "",
            "CSV (*.csv);;All files (*)",
        )
        if path:
            self.telemetry_file_path.setText(path)

    def get_telemetry_source(self) -> tuple[str, str]:
        """Return (source_type, file_path) for TelemetryWorker. source_type is 'mock' or 'file'."""
        raw = self.telemetry_source_combo.currentData()
        source = str(raw).strip().lower() if raw in ("mock", "file") else "mock"
        path = (self.telemetry_file_path.text() or "").strip()
        return source, path

    def get_config_values(self) -> dict:
        return {
            "mass": float(self.mass.value()),
            "cd": float(self.cd.value()),
            "area": float(self.area.value()),
            "uav_x": float(self.uav_x.value()),
            "uav_y": float(self.uav_y.value()),
            "uav_altitude": float(self.uav_altitude.value()),
            "uav_vx": float(self.uav_vx.value()),
            "target_x": float(self.target_x.value()),
            "target_y": float(self.target_y.value()),
            "target_radius": float(self.target_radius.value()),
            "wind_x": float(self.wind_x.value()),
            "wind_std": float(self.wind_std.value()),
            "n_samples": int(self.num_samples.value()),
            "random_seed": int(self.random_seed.value()),
            "threshold_pct": float(self.threshold_pct.value()),
            "system_mode": self._system_mode,
            "auto_interval": str(self.auto_eval_combo.currentText()),
        }
