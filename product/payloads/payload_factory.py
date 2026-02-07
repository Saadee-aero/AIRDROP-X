from .payload_base import Payload
from . import simple_shapes


def create_payload(shape, mass, **kwargs):
    """
    Create a Payload instance from shape type and parameters.
    shape: "box" | "cylinder" | "sphere"
    mass: kg (SI)
    kwargs: box -> length, width, height (m); cylinder -> radius, height (m); sphere -> radius (m)
    """
    shape = str(shape).strip().lower()
    mass = float(mass)
    if mass <= 0:
        raise ValueError("mass must be positive")

    if shape == "box":
        length = kwargs.get("length")
        width = kwargs.get("width")
        height = kwargs.get("height")
        if length is None or width is None or height is None:
            raise ValueError("box requires length, width, height")
        reference_area, drag_coefficient = simple_shapes.box_params(
            length, width, height
        )
    elif shape == "cylinder":
        radius = kwargs.get("radius")
        height = kwargs.get("height")
        if radius is None or height is None:
            raise ValueError("cylinder requires radius, height")
        reference_area, drag_coefficient = simple_shapes.cylinder_params(
            radius, height
        )
    elif shape == "sphere":
        radius = kwargs.get("radius")
        if radius is None:
            raise ValueError("sphere requires radius")
        reference_area, drag_coefficient = simple_shapes.sphere_params(radius)
    else:
        raise ValueError(f"unknown shape: {shape}")

    return Payload(
        mass=mass,
        drag_coefficient=drag_coefficient,
        reference_area=reference_area,
    )
