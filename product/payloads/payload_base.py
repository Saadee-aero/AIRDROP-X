class Payload:
    """
    Payload data structure for engine parameterization.
    SI units: mass (kg), reference_area (m^2), drag_coefficient (dimensionless).
    """

    def __init__(self, mass, drag_coefficient, reference_area):
        self._mass = None
        self._drag_coefficient = None
        self._reference_area = None
        self.mass = mass
        self.drag_coefficient = drag_coefficient
        self.reference_area = reference_area

    @property
    def mass(self):
        return self._mass

    @mass.setter
    def mass(self, value):
        v = float(value)
        if v <= 0:
            raise ValueError("mass must be positive")
        self._mass = v

    @property
    def drag_coefficient(self):
        return self._drag_coefficient

    @drag_coefficient.setter
    def drag_coefficient(self, value):
        v = float(value)
        if v <= 0:
            raise ValueError("drag_coefficient must be positive")
        self._drag_coefficient = v

    @property
    def reference_area(self):
        return self._reference_area

    @reference_area.setter
    def reference_area(self, value):
        v = float(value)
        if v <= 0:
            raise ValueError("reference_area must be positive")
        self._reference_area = v
