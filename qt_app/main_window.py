"""AIRDROP-X Phase 1 PySide6 main window shell."""

from __future__ import annotations

from datetime import datetime
import time

from PySide6.QtCore import QThread, QTimer, Signal, Slot
from PySide6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from adapter import run_simulation_snapshot
from side_panel import MissionConfigPanel
from telemetry import TelemetryWorker
from widgets import StatusStrip
from product.ui import qt_bridge
from product.ui.tabs import (
    analysis as analysis_tab_renderer,
    mission_overview as mission_overview_tab_renderer,
    payload_library,
    sensor_telemetry,
    system_status,
)


class SimulationWorker(QThread):
    """One-shot simulation worker to keep UI responsive."""

    simulation_done = Signal(dict, str)
    simulation_failed = Signal(str, str)

    def __init__(self, config_override: dict, trigger: str, parent=None) -> None:
        super().__init__(parent)
        self.config_override = dict(config_override or {})
        self.trigger = trigger

    def run(self) -> None:
        try:
            snapshot = run_simulation_snapshot(
                config_override=self.config_override,
                include_advisory=True,
            )
            self.simulation_done.emit(snapshot, self.trigger)
        except Exception as exc:  # pragma: no cover - defensive path
            self.simulation_failed.emit(str(exc), self.trigger)


class MainWindow(QMainWindow):
    """Phase 1 desktop shell: structure + placeholders only."""

    def __init__(self) -> None:
        super().__init__()
        self.current_mode = "operator"
        self.system_mode = "SNAPSHOT"
        self.current_snapshot_id = None
        self.snapshot_active = False
        self.telemetry_worker = None
        self.simulation_running = False
        self._simulation_worker = None
        self._last_eval_time = None
        self._latest_snapshot = None
        self._snapshot_created_at = None
        self._last_telemetry = {}
        self._zoom_by_mode = {"operator": 1.0, "engineering": 1.0}
        self._simulation_started_at = None
        self.auto_evaluate_paused = False

        self.auto_timer = QTimer(self)
        self.auto_timer.timeout.connect(self.auto_evaluate)

        self.setWindowTitle("AIRDROP-X")
        self.setMinimumSize(1200, 800)
        self._build_ui()
        self._apply_theme()
        self._refresh_mode_buttons()
        self._start_telemetry()

    def _build_ui(self) -> None:
        central = QWidget(self)
        root = QHBoxLayout(central)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(12)

        # Left mission configuration panel.
        self.left_panel = MissionConfigPanel(central)
        self.system_mode = self.left_panel.system_mode()
        self.left_panel.system_mode_combo.currentTextChanged.connect(self._on_system_mode_changed)
        root.addWidget(self.left_panel)

        # Right side: controls, plot placeholder, bottom status strip.
        right_container = QWidget(central)
        right_layout = QVBoxLayout(right_container)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(10)

        top_controls = QWidget(right_container)
        top_layout = QHBoxLayout(top_controls)
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(8)

        self.operator_btn = QPushButton("OPERATOR", top_controls)
        self.operator_btn.setCheckable(True)
        self.operator_btn.clicked.connect(lambda: self._set_mode("operator"))
        top_layout.addWidget(self.operator_btn)

        self.engineering_btn = QPushButton("ENGINEERING", top_controls)
        self.engineering_btn.setCheckable(True)
        self.engineering_btn.clicked.connect(lambda: self._set_mode("engineering"))
        top_layout.addWidget(self.engineering_btn)

        self.evaluate_btn = QPushButton("Evaluate", top_controls)
        self.evaluate_btn.clicked.connect(self._on_evaluate_clicked)
        top_layout.addWidget(self.evaluate_btn)

        self.zoom_label = QLabel("View Zoom", top_controls)
        top_layout.addWidget(self.zoom_label)
        self.zoom_spin = QDoubleSpinBox(top_controls)
        self.zoom_spin.setDecimals(2)
        self.zoom_spin.setSingleStep(0.05)
        self.zoom_spin.valueChanged.connect(self._on_zoom_changed)
        top_layout.addWidget(self.zoom_spin)

        top_layout.addStretch(1)
        right_layout.addWidget(top_controls)

        self.main_tabs = QTabWidget(right_container)
        self.main_tabs.setObjectName("mainTabs")
        self.main_tabs.tabBar().setExpanding(False)

        self.mission_tab, self.mission_fig, self.mission_canvas = self._build_canvas_tab(self.main_tabs)

        self.payload_tab, self.payload_fig, self.payload_canvas = self._build_payload_tab(self.main_tabs)
        self.telemetry_tab, self.telemetry_fig, self.telemetry_canvas = self._build_canvas_tab(self.main_tabs)

        self.analysis_tab, self.analysis_fig, self.analysis_canvas = self._build_canvas_tab(self.main_tabs)

        self.system_tab, self.system_fig, self.system_canvas = self._build_canvas_tab(self.main_tabs)

        self.main_tabs.addTab(self.mission_tab, "Mission Overview")
        self.main_tabs.addTab(self.payload_tab, "Payload Library")
        self.main_tabs.addTab(self.telemetry_tab, "Sensor & Telemetry")
        self.main_tabs.addTab(self.analysis_tab, "Analysis")
        self.main_tabs.addTab(self.system_tab, "System Status")
        right_layout.addWidget(self.main_tabs, 1)

        self.status_strip = StatusStrip(right_container)
        right_layout.addWidget(self.status_strip)

        root.addWidget(right_container, 1)
        self.setCentralWidget(central)
        self.left_panel.set_snapshot_id("---")
        self.left_panel.apply_state(self.system_mode, False)
        self.left_panel.auto_eval_combo.currentTextChanged.connect(self._on_auto_eval_changed)
        self.left_panel.threshold_pct.valueChanged.connect(self._on_threshold_changed)
        self.left_panel.random_seed.valueChanged.connect(lambda _: self._render_system_tab())
        self.left_panel.num_samples.valueChanged.connect(lambda _: self._render_system_tab())
        self._sync_zoom_widget_from_mode()
        self._update_evaluate_button_text()
        self.status_strip.snapshot_label.setText("Snapshot ID: --- | Ready")
        self.status_strip.telemetry_label.setText("Telemetry: LIVE")
        self.left_panel.set_telemetry_health(0.0, 0.0, "LIVE")
        self.left_panel.set_simulation_age(None)
        self.left_panel.set_auto_evaluate_paused(False)
        self.left_panel.telemetry_source_apply_requested.connect(self._on_telemetry_source_apply)
        self._render_mission_tab()
        self._render_analysis_tab()
        self._render_payload_tab()
        self._render_sensor_tab()
        self._render_system_tab()

    def _build_canvas_tab(self, parent: QWidget) -> tuple[QWidget, object, object]:
        tab = QWidget(parent)
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(0)
        fig = qt_bridge.create_figure(figsize=(9.5, 5.8))
        canvas = qt_bridge.create_canvas(fig)
        layout.addWidget(canvas, 1)
        return tab, fig, canvas

    def _build_payload_tab(self, parent: QWidget) -> tuple[QWidget, object, object]:
        tab = QWidget(parent)
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(6)
        toolbar = QWidget(tab)
        tlay = QHBoxLayout(toolbar)
        tlay.setContentsMargins(4, 4, 4, 4)
        tlay.setSpacing(8)
        tlay.addWidget(QLabel("Category", toolbar))
        self.payload_category_combo = QComboBox(toolbar)
        self.payload_category_combo.addItem("All")
        for c in payload_library.CATEGORIES:
            self.payload_category_combo.addItem(c)
        self.payload_category_combo.currentTextChanged.connect(self._on_payload_category_changed)
        tlay.addWidget(self.payload_category_combo)
        tlay.addWidget(QLabel("Payload", toolbar))
        self.payload_name_combo = QComboBox(toolbar)
        self._refresh_payload_name_combo()
        tlay.addWidget(self.payload_name_combo)
        apply_btn = QPushButton("Apply to mission", toolbar)
        apply_btn.clicked.connect(self._on_payload_apply_clicked)
        tlay.addWidget(apply_btn)
        tlay.addStretch(1)
        layout.addWidget(toolbar)
        fig = qt_bridge.create_figure(figsize=(9.5, 5.4))
        canvas = qt_bridge.create_canvas(fig)
        layout.addWidget(canvas, 1)
        return tab, fig, canvas

    def _refresh_payload_name_combo(self) -> None:
        category = self.payload_category_combo.currentText() if hasattr(self, "payload_category_combo") and self.payload_category_combo else "All"
        self.payload_name_combo.blockSignals(True)
        self.payload_name_combo.clear()
        if category == "All":
            for p in payload_library.PAYLOAD_LIBRARY:
                self.payload_name_combo.addItem(p["name"], p["id"])
        else:
            for _, p in payload_library._payloads_for_category(category):
                self.payload_name_combo.addItem(p["name"], p["id"])
        self.payload_name_combo.blockSignals(False)

    def _on_payload_category_changed(self, _text: str) -> None:
        self._refresh_payload_name_combo()

    def _on_payload_apply_clicked(self) -> None:
        payload_id = self.payload_name_combo.currentData()
        payload_name = self.payload_name_combo.currentText()
        key = payload_id if payload_id is not None else payload_name
        mass, cd, area = payload_library.get_default_physics_for_payload(key)
        self.left_panel.mass.setValue(float(mass))
        self.left_panel.cd.setValue(float(cd))
        self.left_panel.area.setValue(float(area))
        self.status_strip.snapshot_label.setText(
            f"Payload applied: {payload_name} (mass={mass:.1f} kg, Cd={cd:.2f}, A={area:.4f} m²)"
        )

    def _render_mission_tab(self) -> None:
        snapshot = self._latest_snapshot or {}
        impact_points = snapshot.get("impact_points", [])
        p_hit = float(snapshot.get("P_hit", 0.0) or 0.0)
        cep50 = float(snapshot.get("cep50", 0.0) or 0.0)
        threshold = float(self.left_panel.threshold_pct.value())
        advisory = snapshot.get("advisory")
        decision = "DROP" if (p_hit * 100.0) >= threshold else "NO DROP"
        if advisory is not None:
            decision = str(getattr(advisory, "current_feasibility", decision) or decision)

        self.mission_fig.clear()
        ax = self.mission_fig.add_subplot(1, 1, 1)
        mission_overview_tab_renderer.render(
            ax,
            decision=decision,
            target_hit_percentage=p_hit * 100.0,
            cep50=cep50,
            threshold=threshold,
            mode="Balanced",
            impact_points=impact_points,
            confidence_index=snapshot.get("confidence_index"),
            target_position=snapshot.get(
                "target_position",
                (float(self.left_panel.target_x.value()), float(self.left_panel.target_y.value())),
            ),
            target_radius=float(snapshot.get("target_radius", self.left_panel.target_radius.value()) or 0.0),
            advisory_result=advisory,
            release_point=(float(self.left_panel.uav_x.value()), float(self.left_panel.uav_y.value())),
            wind_vector=(float(self.left_panel.wind_x.value()), 0.0),
            dispersion_mode=self.current_mode,
            view_zoom=float(self._zoom_by_mode.get(self.current_mode, 1.0)),
            snapshot_timestamp=(
                self._snapshot_created_at.strftime("%Y-%m-%d %H:%M:%S")
                if self._snapshot_created_at is not None
                else None
            ),
            random_seed=int(self.left_panel.random_seed.value()),
            n_samples=int(self.left_panel.num_samples.value()),
        )
        try:
            self.mission_fig.tight_layout()
        except Exception:
            pass
        self.mission_canvas.draw_idle()

    def _render_analysis_tab(self) -> None:
        snapshot = self._latest_snapshot or {}
        impact_points = snapshot.get("impact_points", [])
        p_hit = float(snapshot.get("P_hit", 0.0) or 0.0)
        cep50 = float(snapshot.get("cep50", 0.0) or 0.0)

        self.analysis_fig.clear()
        ax = self.analysis_fig.add_subplot(1, 1, 1)
        analysis_tab_renderer.render(
            ax,
            impact_points=impact_points,
            target_position=snapshot.get(
                "target_position",
                (float(self.left_panel.target_x.value()), float(self.left_panel.target_y.value())),
            ),
            target_radius=float(snapshot.get("target_radius", self.left_panel.target_radius.value()) or 0.0),
            uav_position=(
                float(self.left_panel.uav_x.value()),
                float(self.left_panel.uav_y.value()),
                float(self.left_panel.uav_altitude.value()),
            ),
            wind_mean=(float(self.left_panel.wind_x.value()), 0.0, 0.0),
            cep50=cep50,
            target_hit_percentage=p_hit * 100.0,
            impact_velocity_stats=snapshot.get("impact_velocity_stats"),
            max_safe_impact_speed=None,
            dispersion_mode=self.current_mode,
            view_zoom=float(self._zoom_by_mode.get(self.current_mode, 1.0)),
            snapshot_timestamp=(
                self._snapshot_created_at.strftime("%Y-%m-%d %H:%M:%S")
                if self._snapshot_created_at is not None
                else None
            ),
            random_seed=int(self.left_panel.random_seed.value()),
            n_samples=int(self.left_panel.num_samples.value()),
        )
        try:
            self.analysis_fig.tight_layout()
        except Exception:
            pass
        self.analysis_canvas.draw_idle()

    def _render_payload_tab(self) -> None:
        self.payload_fig.clear()
        ax = self.payload_fig.add_subplot(1, 1, 1)
        payload_library.render(ax, self.payload_fig, interactive=False)
        self.payload_canvas.draw_idle()

    def _render_sensor_tab(self) -> None:
        self.telemetry_fig.clear()
        ax = self.telemetry_fig.add_subplot(1, 1, 1)
        wind_x = float(self.left_panel.wind_x.value())
        wind_std = float(self.left_panel.wind_std.value())
        uav_alt = float(self.left_panel.uav_altitude.value())
        uav_vx = float(self.left_panel.uav_vx.value())
        telem_age = float(self._last_telemetry.get("age_s", 0.0) or 0.0)
        telem_status = str(self._last_telemetry.get("status", "Fresh"))
        wind_speed = abs(wind_x)
        wind_dir = 0.0 if wind_x >= 0 else 180.0
        wind_conf = "High" if telem_status == "Fresh" else ("Medium" if telem_status == "Delay" else "Low")
        source = "Telemetry" if self.system_mode == "LIVE" else "Assumed Gaussian"

        sensor_telemetry.render(
            ax,
            gnss_speed_ms=uav_vx,
            gnss_heading_deg=0.0,
            gnss_altitude_m=uav_alt,
            gnss_fix="3D Fix",
            gnss_freshness_s=telem_age if self.system_mode == "LIVE" else None,
            wind_dir_deg=wind_dir,
            wind_speed_ms=wind_speed,
            wind_uncertainty=wind_std,
            wind_source=source,
            wind_confidence=wind_conf,
            wind_mean_ms=wind_x,
            wind_std_dev_ms=wind_std,
            telemetry_live=(self.system_mode == "LIVE"),
        )
        try:
            self.telemetry_fig.tight_layout()
        except Exception:
            pass
        self.telemetry_canvas.draw_idle()

    def _render_system_tab(self) -> None:
        from configs import mission_configs as cfg

        self.system_fig.clear()
        ax = self.system_fig.add_subplot(1, 1, 1)
        warnings = ["No active warnings."]
        if self.system_mode == "LIVE" and self.auto_evaluate_paused:
            warnings = ["Auto-evaluate paused due to performance threshold (>1.5s run)."]
        system_status.render(
            ax,
            random_seed=int(self.left_panel.random_seed.value()),
            n_samples=int(self.left_panel.num_samples.value()),
            dt=float(cfg.dt),
            snapshot_created_at=self._snapshot_created_at,
            warnings=warnings,
        )
        try:
            self.system_fig.tight_layout()
        except Exception:
            pass
        self.system_canvas.draw_idle()

    def _apply_theme(self) -> None:
        self.setStyleSheet(
            """
            QMainWindow {
                background-color: #050905;
            }
            QWidget {
                color: #86a886;
                font-family: Consolas, "Courier New", monospace;
                font-size: 12px;
            }
            QWidget#leftPanel, QFrame#plotPlaceholder, QFrame#statusStrip {
                background-color: #0a110a;
                border: 1px solid #1c2d1c;
                border-radius: 4px;
            }
            QLabel#panelTitle {
                color: #2cff05;
                font-weight: bold;
                letter-spacing: 1px;
            }
            QFrame#configGroup {
                background-color: #0d140d;
                border: 1px solid #1e2f1e;
                border-radius: 4px;
            }
            QLabel#groupTitle {
                color: #2cff05;
                font-weight: bold;
            }
            QLabel#panelFieldValue {
                color: #6c8f6a;
            }
            QLabel#panelSubtitle, QLabel#placeholderLine, QLabel#statusLabel {
                color: #6c8f6a;
            }
            QLabel#plotPlaceholderText {
                color: #6c8f6a;
                font-size: 14px;
                letter-spacing: 1px;
            }
            QPushButton, QAbstractSpinBox, QComboBox {
                min-height: 34px;
                padding: 6px 12px;
                background-color: #0b120b;
                color: #6c8f6a;
                border: 1px solid #1a2a1a;
                border-radius: 4px;
                font-weight: normal;
            }
            QPushButton:hover, QAbstractSpinBox:hover, QComboBox:hover {
                border: 1px solid #2f4a2f;
            }
            QComboBox QAbstractItemView {
                background: #0b120b;
                color: #6c8f6a;
                selection-background-color: #133013;
            }
            QTabWidget#mainTabs::pane {
                border: 1px solid #1a2a1a;
                background: #0a110a;
                margin-top: 6px;
            }
            QTabWidget#mainTabs::tab-bar {
                alignment: center;
            }
            QTabBar::tab {
                min-width: 150px;
                min-height: 34px;
                padding: 8px 12px;
                margin-right: 8px;
                background-color: #0b120b;
                color: #6c8f6a;
                border: 1px solid #1a2a1a;
                border-bottom: none;
                font-weight: normal;
            }
            QTabBar::tab:selected {
                color: #2cff05;
                border: 1px solid #2cff05;
                border-bottom: 2px solid #2cff05;
                font-weight: bold;
            }
            QAbstractSpinBox::up-button, QAbstractSpinBox::down-button {
                width: 14px;
                border: none;
                background: #122012;
            }
            QPushButton:checked {
                color: #2cff05;
                border: 2px solid #2cff05;
                background-color: rgba(44, 255, 5, 0.08);
                font-weight: bold;
            }
            """
        )

    def _set_mode(self, mode: str) -> None:
        self.current_mode = mode
        self._refresh_mode_buttons()
        self._sync_zoom_widget_from_mode()
        self._render_mission_tab()
        self._render_analysis_tab()
        if self.snapshot_active:
            self.status_strip.snapshot_label.setText(
                f"Snapshot ID: {self.current_snapshot_id or '---'} | Locked | Mode: {mode.title()}"
            )
        else:
            self.status_strip.snapshot_label.setText(
                f"Snapshot ID: {self.current_snapshot_id or '---'} | Editable | Mode: {mode.title()}"
            )

    def _refresh_mode_buttons(self) -> None:
        is_operator = self.current_mode == "operator"
        self.operator_btn.setChecked(is_operator)
        self.engineering_btn.setChecked(not is_operator)

    def _sync_zoom_widget_from_mode(self) -> None:
        if self.current_mode == "engineering":
            mn, mx = 0.60, 1.80
        else:
            mn, mx = 0.60, 2.20
        value = float(self._zoom_by_mode.get(self.current_mode, 1.0))
        value = max(mn, min(mx, value))
        self.zoom_spin.blockSignals(True)
        self.zoom_spin.setRange(mn, mx)
        self.zoom_spin.setValue(value)
        self.zoom_spin.blockSignals(False)

    @Slot(float)
    def _on_zoom_changed(self, value: float) -> None:
        self._zoom_by_mode[self.current_mode] = float(value)
        self._render_mission_tab()
        self._render_analysis_tab()

    def _update_evaluate_button_text(self) -> None:
        if self.snapshot_active:
            self.evaluate_btn.setText("Modify & Re-run")
            return
        if self.system_mode == "LIVE":
            self.evaluate_btn.setText("Evaluate with Current Telemetry")
            return
        self.evaluate_btn.setText("Evaluate Simulation")

    @Slot(float)
    def _on_threshold_changed(self, _value: float) -> None:
        self._render_mission_tab()

    @Slot(str)
    def _on_system_mode_changed(self, mode: str) -> None:
        raw = str(mode or "SNAPSHOT").strip().upper()
        if raw.startswith("LIVE"):
            next_mode = "LIVE"
        elif raw.startswith("SNAP"):
            next_mode = "SNAPSHOT"
        else:
            next_mode = self.left_panel.system_mode()
            if next_mode not in ("SNAPSHOT", "LIVE"):
                next_mode = "SNAPSHOT"
        self.system_mode = next_mode
        self.left_panel.set_system_mode(next_mode)
        self.auto_evaluate_paused = False
        self.left_panel.set_auto_evaluate_paused(False)
        if next_mode != "LIVE":
            self.auto_timer.stop()
        else:
            self._apply_live_telemetry_to_panel()
        self._update_evaluate_button_text()
        self._render_sensor_tab()

    @Slot(str)
    def _on_auto_eval_changed(self, value: str) -> None:
        if self.system_mode != "LIVE":
            self.auto_timer.stop()
            return
        value_norm = str(value).strip().upper()
        if value_norm == "OFF":
            self.auto_timer.stop()
            self.auto_evaluate_paused = False
            self.left_panel.set_auto_evaluate_paused(False)
            return
        if value_norm == "1S":
            self.auto_timer.start(1000)
            self.left_panel.set_auto_evaluate_paused(self.auto_evaluate_paused)
            return
        if value_norm == "2S":
            self.auto_timer.start(2000)
            self.left_panel.set_auto_evaluate_paused(self.auto_evaluate_paused)

    @Slot()
    def auto_evaluate(self) -> None:
        if self.system_mode != "LIVE":
            return
        if self.auto_evaluate_paused:
            return
        if not self.snapshot_active:
            return
        if self.simulation_running:
            return
        self._update_simulation_age()
        self._start_simulation(trigger="auto")

    def _on_evaluate_clicked(self) -> None:
        if self.simulation_running:
            self.status_strip.snapshot_label.setText("Snapshot: Simulation already running...")
            return

        if not self.snapshot_active:
            if self.system_mode == "LIVE":
                self.status_strip.snapshot_label.setText("Snapshot: Evaluating with live telemetry...")
            else:
                self.status_strip.snapshot_label.setText("Snapshot: Evaluating...")
            self._start_simulation(trigger="manual_lock")
            return

        # Unlock only; do not run simulation.
        self.left_panel.set_read_only(False)
        self.snapshot_active = False
        self._update_evaluate_button_text()
        self.status_strip.snapshot_label.setText(
            f"Snapshot ID: {self.current_snapshot_id or '---'} | Unlocked | Modify and Evaluate"
        )

    def _start_simulation(self, trigger: str) -> None:
        if self.simulation_running:
            return
        self.simulation_running = True
        self._simulation_started_at = time.time()
        cfg = self.left_panel.get_config_values()
        worker = SimulationWorker(cfg, trigger, self)
        worker.simulation_done.connect(self._on_simulation_done)
        worker.simulation_failed.connect(self._on_simulation_failed)
        worker.finished.connect(self._on_simulation_finished)
        self._simulation_worker = worker
        worker.start()

    @Slot(dict, str)
    def _on_simulation_done(self, snapshot: dict, trigger: str) -> None:
        self._latest_snapshot = dict(snapshot or {})
        self._snapshot_created_at = datetime.now()
        self.current_snapshot_id = self._snapshot_created_at.strftime("AX-%Y%m%d-%H%M%S")
        self._last_eval_time = time.time()
        run_duration_sec = None
        if self._simulation_started_at is not None:
            run_duration_sec = max(0.0, self._last_eval_time - self._simulation_started_at)
        self._update_simulation_age()
        self.left_panel.set_snapshot_id(self.current_snapshot_id)
        self._render_mission_tab()
        self._render_analysis_tab()
        self._render_system_tab()

        if (
            run_duration_sec is not None
            and run_duration_sec > 1.5
            and self.system_mode == "LIVE"
            and str(self.left_panel.auto_eval_combo.currentText()).upper() != "OFF"
        ):
            self.auto_evaluate_paused = True
            self.auto_timer.stop()
            self.left_panel.set_auto_evaluate_paused(True)

        if trigger == "manual_lock":
            self.left_panel.set_read_only(True)
            self.snapshot_active = True
            self._update_evaluate_button_text()
            self.status_strip.snapshot_label.setText(
                f"Snapshot ID: {self.current_snapshot_id} | Locked | P_hit: {float(snapshot.get('P_hit', 0.0)) * 100.0:.1f}%"
            )
            return

        if trigger == "auto":
            self.status_strip.snapshot_label.setText(
                f"Snapshot ID: {self.current_snapshot_id} | Auto-updated | P_hit: {float(snapshot.get('P_hit', 0.0)) * 100.0:.1f}%"
            )
            return

        self.status_strip.snapshot_label.setText(
            f"Snapshot ID: {self.current_snapshot_id} | Updated"
        )

    @Slot(str, str)
    def _on_simulation_failed(self, error: str, trigger: str) -> None:  # noqa: ARG002
        short = (error or "unknown error").strip()
        self.status_strip.snapshot_label.setText(f"Snapshot: Failed ({short[:72]})")

    @Slot()
    def _on_simulation_finished(self) -> None:
        self.simulation_running = False
        self._simulation_started_at = None
        if self._simulation_worker is not None:
            self._simulation_worker.deleteLater()
            self._simulation_worker = None

    def _start_telemetry(self, source: str = "mock", file_path: str | None = None) -> None:
        if self.telemetry_worker is not None:
            self.telemetry_worker.stop()
            self.telemetry_worker.wait(1500)
            self.telemetry_worker = None
        self.telemetry_worker = TelemetryWorker(self, source=source, file_path=file_path or None)
        self.telemetry_worker.telemetry_updated.connect(self.handle_telemetry)
        self.telemetry_worker.start()
        self.status_strip.telemetry_label.setText("Telemetry: LIVE")

    def _on_telemetry_source_apply(self) -> None:
        source, path = self.left_panel.get_telemetry_source()
        self._start_telemetry(source=source, file_path=path if path else None)
        self.status_strip.telemetry_label.setText(
            "Telemetry: LIVE (file)" if source == "file" and path else "Telemetry: LIVE"
        )

    def _update_simulation_age(self) -> None:
        if self._last_eval_time is None:
            self.left_panel.set_simulation_age(None)
            return
        self.left_panel.set_simulation_age(max(0.0, time.time() - self._last_eval_time))

    def _apply_live_telemetry_to_panel(self) -> None:
        data = self._last_telemetry or {}
        if not data:
            return
        self.left_panel.uav_x.setValue(float(data.get("x", self.left_panel.uav_x.value())))
        self.left_panel.uav_y.setValue(float(data.get("y", self.left_panel.uav_y.value())))
        self.left_panel.uav_altitude.setValue(float(data.get("z", self.left_panel.uav_altitude.value())))
        self.left_panel.uav_vx.setValue(float(data.get("vx", self.left_panel.uav_vx.value())))
        self.left_panel.wind_x.setValue(float(data.get("wind_x", self.left_panel.wind_x.value())))
        self.left_panel.wind_std.setValue(float(data.get("wind_std", self.left_panel.wind_std.value())))

    @Slot(dict)
    def handle_telemetry(self, data: dict) -> None:
        self._last_telemetry = dict(data or {})
        if self.system_mode == "LIVE":
            self._apply_live_telemetry_to_panel()
        packet_rate = float(data.get("packet_rate_hz", 2.0))
        age_s = float(data.get("age_s", 0.5))
        status = str(data.get("status", "LIVE"))
        self.left_panel.set_telemetry_health(packet_rate, age_s, status)
        self._update_simulation_age()
        if self.main_tabs.currentIndex() == 2:
            self._render_sensor_tab()
        self.status_strip.telemetry_label.setText("Telemetry: LIVE")

    def closeEvent(self, event) -> None:  # noqa: N802
        self.auto_timer.stop()
        if self._simulation_worker is not None and self._simulation_worker.isRunning():
            self._simulation_worker.wait(3000)

        if self.telemetry_worker is not None:
            self.telemetry_worker.stop()
            self.telemetry_worker.wait(1500)
        self.status_strip.telemetry_label.setText("Telemetry: STOPPED")
        super().closeEvent(event)
