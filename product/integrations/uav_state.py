"""
Internal UAV state representation. SI units.
Used by log replay, telemetry ingest, and MAVLink adapter.
"""


class UAVStateSnapshot:
    """
    Read-only snapshot: time, position (m), velocity (m/s).
    position: (x, y, z) in m. altitude is position[2].
    velocity: (vx, vy, vz) in m/s.
    time_s: timestamp in seconds (monotonic or boot time).
    """

    __slots__ = ("_time_s", "_position", "_velocity")

    def __init__(self, time_s, position, velocity):
        self._time_s = float(time_s)
        self._position = (
            float(position[0]),
            float(position[1]),
            float(position[2]),
        )
        self._velocity = (
            float(velocity[0]),
            float(velocity[1]),
            float(velocity[2]),
        )

    @property
    def time_s(self):
        return self._time_s

    @property
    def position(self):
        return self._position

    @property
    def velocity(self):
        return self._velocity

    @property
    def altitude(self):
        return self._position[2]
