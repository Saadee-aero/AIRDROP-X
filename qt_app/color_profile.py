"""
Color profile hook: adjust intensity based on mission_mode.
TACTICAL: higher saturation
HUMANITARIAN: slightly softer tone
Does not alter decision-to-color mapping; only intensity.
"""
from __future__ import annotations

import colorsys


def _hex_to_rgb(hex_str: str) -> tuple[float, float, float]:
    h = hex_str.lstrip("#")
    if len(h) == 6:
        return tuple(int(h[i : i + 2], 16) / 255.0 for i in (0, 2, 4))
    return (0.5, 0.5, 0.5)


def _rgb_to_hex(r: float, g: float, b: float) -> str:
    return "#{:02x}{:02x}{:02x}".format(
        int(max(0, min(1, r)) * 255),
        int(max(0, min(1, g)) * 255),
        int(max(0, min(1, b)) * 255),
    )


def adjust_color_intensity(hex_color: str, mission_mode: str) -> str:
    """
    Adjust color intensity based on mission mode.
    TACTICAL: saturation *= 1.15 (higher saturation)
    HUMANITARIAN: saturation *= 0.88 (softer tone)
    """
    mode = str(mission_mode or "TACTICAL").strip().upper()
    if mode == "TACTICAL":
        sat_mult = 1.15
    elif mode == "HUMANITARIAN":
        sat_mult = 0.88
    else:
        return hex_color
    r, g, b = _hex_to_rgb(hex_color)
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    s_adj = min(1.0, s * sat_mult)
    r2, g2, b2 = colorsys.hsv_to_rgb(h, s_adj, v)
    return _rgb_to_hex(r2, g2, b2)
