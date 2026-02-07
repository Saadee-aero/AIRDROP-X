"""
Translate MAVLink-style messages to internal UAV state. Hides protocol details.
Accepts dict representation of messages (no pymavlink dependency required).
No engine or product internals dependency.
"""

import math

from .uav_state import UAVStateSnapshot

LOCAL_POSITION_NED_MSG = "LOCAL_POSITION_NED"
GLOBAL_POSITION_INT_MSG = "GLOBAL_POSITION_INT"


def from_local_position_ned(msg):
    """
    Convert LOCAL_POSITION_NED-style dict to UAVStateSnapshot.
    msg: dict with time_boot_ms, x, y, z (m), vx, vy, vz (m/s).
    """
    t_ms = msg.get("time_boot_ms", 0)
    time_s = float(t_ms) / 1000.0
    x = float(msg.get("x", 0))
    y = float(msg.get("y", 0))
    z = float(msg.get("z", 0))
    vx = float(msg.get("vx", 0))
    vy = float(msg.get("vy", 0))
    vz = float(msg.get("vz", 0))
    return UAVStateSnapshot(time_s, (x, y, z), (vx, vy, vz))


def from_global_position_int(msg, ref_lat_deg=None, ref_lon_deg=None):
    """
    Convert GLOBAL_POSITION_INT-style dict to UAVStateSnapshot (local NED approximation).
    msg: dict with time_boot_ms, lat, lon (1e7 deg), alt (mm), vx, vy, vz (cm/s).
    ref_lat_deg, ref_lon_deg: optional reference for lat/lon -> local x,y (m). If None, x=y=0.
    """
    t_ms = msg.get("time_boot_ms", 0)
    time_s = float(t_ms) / 1000.0
    lat = float(msg.get("lat", 0)) / 1e7
    lon = float(msg.get("lon", 0)) / 1e7
    alt_mm = float(msg.get("alt", msg.get("relative_alt", 0)))
    alt_m = alt_mm / 1000.0
    vx = float(msg.get("vx", 0)) / 100.0  # cm/s -> m/s
    vy = float(msg.get("vy", 0)) / 100.0
    vz = float(msg.get("vz", 0)) / 100.0
    if ref_lat_deg is not None and ref_lon_deg is not None:
        m_per_deg_lat = 111320.0
        m_per_deg_lon = 111320.0 * math.cos(math.radians(ref_lat_deg))
        x = (lon - ref_lon_deg) * m_per_deg_lon
        y = (lat - ref_lat_deg) * m_per_deg_lat
        z = alt_m
    else:
        x, y, z = 0.0, 0.0, alt_m
    return UAVStateSnapshot(time_s, (x, y, z), (vx, vy, vz))


def mavlink_to_uav_state(msg, msg_type=None):
    """
    Translate a MAVLink message (dict) to UAVStateSnapshot.
    msg_type: "LOCAL_POSITION_NED" | "GLOBAL_POSITION_INT" | None (auto-detect).
    For GLOBAL_POSITION_INT, pass ref_lat_deg and ref_lon_deg in msg as _ref_lat_deg, _ref_lon_deg if needed.
    """
    if msg_type is None:
        msg_type = msg.get("_type", msg.get("mavpacket_type", ""))
    if msg_type == LOCAL_POSITION_NED_MSG or ("x" in msg and "y" in msg and "z" in msg and "vx" in msg):
        return from_local_position_ned(msg)
    if msg_type == GLOBAL_POSITION_INT_MSG or ("lat" in msg and "lon" in msg):
        ref_lat = msg.get("_ref_lat_deg")
        ref_lon = msg.get("_ref_lon_deg")
        return from_global_position_int(msg, ref_lat, ref_lon)
    return from_local_position_ned(msg)
