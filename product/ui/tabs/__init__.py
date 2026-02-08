"""
Tab modules for AIRDROP-X UI. Each tab exposes render(ax).
"""

from .mission_overview import render as render_mission_overview
from .payload_library import render as render_payload_library
from .sensor_telemetry import render as render_sensor_telemetry
from .analysis import render as render_analysis
from .system_status import render as render_system_status

TABS = [
    ("Mission Overview", render_mission_overview),
    ("Payload Library", render_payload_library),
    ("Sensor & Telemetry", render_sensor_telemetry),
    ("Analysis", render_analysis),
    ("System Status", render_system_status),
]
