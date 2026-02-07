class Environment:
    """
    Environmental parameters for mission context.
    SI units: wind_mean (m/s), wind_std (m/s).
    """

    def __init__(self, wind_mean, wind_std):
        self._wind_mean = None
        self._wind_std = None
        self.wind_mean = wind_mean
        self.wind_std = wind_std

    @property
    def wind_mean(self):
        return self._wind_mean

    @wind_mean.setter
    def wind_mean(self, value):
        v = (float(value[0]), float(value[1]), float(value[2]))
        self._wind_mean = v

    @property
    def wind_std(self):
        return self._wind_std

    @wind_std.setter
    def wind_std(self, value):
        v = float(value)
        if v < 0:
            raise ValueError("wind_std must be non-negative")
        self._wind_std = v
