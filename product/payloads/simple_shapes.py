import math

BOX_DRAG_COEFFICIENT = 1.2
CYLINDER_DRAG_COEFFICIENT = 1.0
SPHERE_DRAG_COEFFICIENT = 0.47

# Constant Cd values for subsonic bluff bodies; not Reynolds-dependent.
# Box: rectangular prism, face-on; Cylinder: axis aligned with flow; Sphere: standard.


def box_reference_area(length, width, height):
    """Reference area = length * width (horizontal cross-section when falling flat). SI: m."""
    length = float(length)
    width = float(width)
    height = float(height)
    if length <= 0 or width <= 0 or height <= 0:
        raise ValueError("length, width, height must be positive")
    return length * width


def box_drag_coefficient():
    """Constant drag coefficient for a rectangular box (face-on), subsonic bluff body."""
    return BOX_DRAG_COEFFICIENT


def cylinder_reference_area(radius, height):
    """Reference area = pi * radius^2 (circular cross-section, axis vertical). SI: m."""
    radius = float(radius)
    height = float(height)
    if radius <= 0 or height <= 0:
        raise ValueError("radius and height must be positive")
    return math.pi * radius * radius


def cylinder_drag_coefficient():
    """Constant drag coefficient for a circular cylinder (axis along flow), subsonic bluff body."""
    return CYLINDER_DRAG_COEFFICIENT


def sphere_reference_area(radius):
    """Reference area = pi * radius^2 (cross-sectional area). SI: m."""
    radius = float(radius)
    if radius <= 0:
        raise ValueError("radius must be positive")
    return math.pi * radius * radius


def sphere_drag_coefficient():
    """Constant drag coefficient for a sphere, subsonic bluff body."""
    return SPHERE_DRAG_COEFFICIENT


def box_params(length, width, height):
    """Return (reference_area, drag_coefficient) for a box. SI: m."""
    return (box_reference_area(length, width, height), box_drag_coefficient())


def cylinder_params(radius, height):
    """Return (reference_area, drag_coefficient) for a cylinder. SI: m."""
    return (cylinder_reference_area(radius, height), cylinder_drag_coefficient())


def sphere_params(radius):
    """Return (reference_area, drag_coefficient) for a sphere. SI: m."""
    return (sphere_reference_area(radius), sphere_drag_coefficient())
