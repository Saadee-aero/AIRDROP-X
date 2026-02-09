"""
Load flight log files and yield UAV state snapshots for deterministic replay.
No physics, no control. Read-only.
"""

import csv
import json
import os

from .uav_state import UAVStateSnapshot


def _parse_row_csv(row, time_key, pos_keys, vel_keys):
    """Build (time_s, position, velocity) from a CSV row dict."""
    time_s = float(row.get(time_key, 0))
    x = float(row.get(pos_keys[0], 0))
    y = float(row.get(pos_keys[1], 0))
    z = float(row.get(pos_keys[2], 0))
    vx = float(row.get(vel_keys[0], 0))
    vy = float(row.get(vel_keys[1], 0))
    vz = float(row.get(vel_keys[2], 0))
    return (time_s, (x, y, z), (vx, vy, vz))


def _detect_csv_columns(reader):
    """Return (time_key, pos_keys, vel_keys) from header. Prefer time_s, x/y/z, vx/vy/vz."""
    header = [h.strip().lower() for h in reader.fieldnames]
    time_candidates = ["time_s", "time", "t", "timestamp"]
    time_key = next((f for f in reader.fieldnames if f.strip().lower() in time_candidates), None)
    if time_key is None and reader.fieldnames:
        # Fallback: try first column, but log a warning or be strict.
        # Strict mode: require explicit time column.
        # time_key = reader.fieldnames[0]  <-- OLD loose behavior
        raise ValueError(
            f"Could not automatically detect time column in CSV header: {reader.fieldnames}. "
            f"Expected one of: {time_candidates}"
        )

    def find_xyz(prefixes, suffixes):
        out = []
        for s in suffixes:
            for p in prefixes:
                cand = p + s
                for f in reader.fieldnames:
                    if f.strip().lower() == cand.lower():
                        out.append(f)
                        break
                else:
                    continue
                break
        return out if len(out) == 3 else None

    pos_keys = find_xyz(["", "position_"], ["x", "y", "z"])
    if not pos_keys:
        pos_keys = find_xyz(["", "pos_"], ["x", "y", "z"])
    if not pos_keys:
        px = next((f for f in reader.fieldnames if f.strip().lower() == "x"), None)
        py = next((f for f in reader.fieldnames if f.strip().lower() == "y"), None)
        pz = next((f for f in reader.fieldnames if f.strip().lower() == "z"), None)
        if px and py and pz:
            pos_keys = [px, py, pz]
    if not pos_keys and len(header) >= 6:
        pos_keys = [reader.fieldnames[1], reader.fieldnames[2], reader.fieldnames[3]]
    vel_keys = find_xyz(["", "velocity_", "v"], ["x", "y", "z"])
    if not vel_keys:
        vx = next((f for f in reader.fieldnames if f.strip().lower() == "vx"), None)
        vy = next((f for f in reader.fieldnames if f.strip().lower() == "vy"), None)
        vz = next((f for f in reader.fieldnames if f.strip().lower() == "vz"), None)
        if vx and vy and vz:
            vel_keys = [vx, vy, vz]
        elif len(reader.fieldnames) >= 7:
            vel_keys = [reader.fieldnames[4], reader.fieldnames[5], reader.fieldnames[6]]
        else:
            vel_keys = ["vx", "vy", "vz"]
    return time_key, pos_keys, vel_keys


def load_replay_csv(filepath):
    """
    Load a CSV flight log. Yields UAVStateSnapshot in time order.
    filepath: path to CSV with header. Columns: time (or time_s), x,y,z (or position_*), vx,vy,vz (or velocity_*).
    Deterministic: same file -> same ordered sequence.
    """
    with open(filepath, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            return
        time_key, pos_keys, vel_keys = _detect_csv_columns(reader)
        rows = list(reader)
    # Deterministic: sort by time
    def time_from_row(r):
        try:
            return float(r.get(time_key, 0))
        except (TypeError, ValueError):
            return 0.0
    rows.sort(key=time_from_row)
    for row in rows:
        try:
            time_s, position, velocity = _parse_row_csv(row, time_key, pos_keys, vel_keys)
            yield UAVStateSnapshot(time_s, position, velocity)
        except (KeyError, TypeError, ValueError):
            continue


def load_replay_json(filepath):
    """
    Load a JSON flight log. Expects array of objects with time_s (or time), position (x,y,z), velocity (vx,vy,vz).
    Yields UAVStateSnapshot in time order. Deterministic.
    """
    with open(filepath, encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        data = data.get("frames", data.get("samples", [data]))
    if not data:
        return

    def to_snapshot(obj):
        if isinstance(obj, dict):
            t = float(obj.get("time_s", obj.get("time", 0)))
            p = obj.get("position", obj)
            if isinstance(p, dict):
                pos = (float(p.get("x", 0)), float(p.get("y", 0)), float(p.get("z", p.get("altitude", 0))))
            else:
                pos = (float(obj.get("x", 0)), float(obj.get("y", 0)), float(obj.get("z", obj.get("altitude", 0))))
            v = obj.get("velocity", obj)
            if isinstance(v, dict):
                vel = (float(v.get("vx", v.get("x", 0))), float(v.get("vy", v.get("y", 0))), float(v.get("vz", v.get("z", 0))))
            else:
                vel = (float(obj.get("vx", 0)), float(obj.get("vy", 0)), float(obj.get("vz", 0)))
            return UAVStateSnapshot(t, pos, vel)
        return None

    snapshots = []
    for item in data:
        try:
            s = to_snapshot(item)
            if s is not None:
                snapshots.append(s)
        except (TypeError, ValueError, KeyError):
            continue
    snapshots.sort(key=lambda s: s.time_s)
    for s in snapshots:
        yield s


def load_replay(filepath):
    """
    Load CSV or JSON flight log. Yields UAVStateSnapshot in time order.
    Deterministic for given filepath.
    """
    path = os.path.abspath(filepath)
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Log file not found: {filepath}")
    ext = os.path.splitext(path)[1].lower()
    if ext == ".json":
        yield from load_replay_json(path)
    else:
        yield from load_replay_csv(path)
