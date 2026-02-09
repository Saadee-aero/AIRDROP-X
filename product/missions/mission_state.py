from .target_manager import Target
from .environment import Environment


class MissionState:
    """
    Aggregates mission context: payload, target, environment, UAV state.
    SI units throughout. No engine imports.
    """

    def __init__(self, payload, target, environment, uav_position, uav_velocity):
        self._payload = None
        self._target = None
        self._environment = None
        self._uav_position = None
        self._uav_velocity = None
        self.payload = payload
        self.target = target
        self.environment = environment
        self.uav_position = uav_position
        self.uav_velocity = uav_velocity

    @property
    def payload(self):
        return self._payload

    @payload.setter
    def payload(self, value):
        if value is None:
            raise ValueError("payload must not be None")
        self._payload = value

    @property
    def target(self):
        return self._target

    @target.setter
    def target(self, value):
        if value is None:
            raise ValueError("target must not be None")
        self._target = value

    @property
    def environment(self):
        return self._environment

    @environment.setter
    def environment(self, value):
        if value is None:
            raise ValueError("environment must not be None")
        self._environment = value

    @property
    def uav_position(self):
        return self._uav_position

    @uav_position.setter
    def uav_position(self, value):
        if value is None:
            raise ValueError("uav_position must not be None")
        if len(value) != 3:
            raise ValueError(f"uav_position must have 3 elements (x, y, z), got {len(value)}")
        v = (float(value[0]), float(value[1]), float(value[2]))
        self._uav_position = v

    @property
    def uav_velocity(self):
        return self._uav_velocity

    @uav_velocity.setter
    def uav_velocity(self, value):
        if value is None:
            raise ValueError("uav_velocity must not be None")
        if len(value) != 3:
            raise ValueError(f"uav_velocity must have 3 elements (vx, vy, vz), got {len(value)}")
        v = (float(value[0]), float(value[1]), float(value[2]))
        self._uav_velocity = v

    def validate(self):
        """Raise if any required component is missing."""
        if self._payload is None:
            raise ValueError("payload is not set")
        if self._target is None:
            raise ValueError("target is not set")
        if self._environment is None:
            raise ValueError("environment is not set")
        if self._uav_position is None:
            raise ValueError("uav_position is not set")
        if self._uav_velocity is None:
            raise ValueError("uav_velocity is not set")

    def export_engine_inputs(self):
        """
        Return a dict of engine-ready inputs (SI).
        Keys match engine parameter names for downstream consumption.
        """
        self.validate()
        return {
            "uav_pos": self._uav_position,
            "uav_vel": self._uav_velocity,
            "target_pos": self._target.position,
            "target_radius": self._target.radius,
            "wind_mean": self._environment.wind_mean,
            "wind_std": self._environment.wind_std,
            "mass": self._payload.mass,
            "A": self._payload.reference_area,
            "Cd": self._payload.drag_coefficient,
        }
