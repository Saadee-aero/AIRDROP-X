import numpy as np


def compute_hit_probability(impact_points, target_position, target_radius):
    """
    Target hit probability from impact points. Inputs must not be empty.
    Returns float in [0, 1].
    """
    impact_points = np.asarray(impact_points, dtype=float)
    target_position = np.asarray(target_position, dtype=float)
    if impact_points.shape[0] == 0:
        raise ValueError("impact_points must not be empty")
    if impact_points.shape[1] != 2:
        raise ValueError("impact_points must have shape (N, 2)")
    target_2d = target_position.reshape(2)
    radius = float(target_radius)
    radial_distances = np.linalg.norm(impact_points - target_2d, axis=1)
    hits = np.sum(radial_distances <= radius)
    return float(hits) / float(impact_points.shape[0])


def compute_cep50(impact_points, target_position):
    """
    CEP50: 50th percentile of radial miss distance from target. Inputs must not be empty.
    Returns CEP50 radius in same units as inputs.
    """
    impact_points = np.asarray(impact_points, dtype=float)
    target_position = np.asarray(target_position, dtype=float)
    if impact_points.shape[0] == 0:
        raise ValueError("impact_points must not be empty")
    if impact_points.shape[1] != 2:
        raise ValueError("impact_points must have shape (N, 2)")
    target_2d = target_position.reshape(2)
    radial_distances = np.linalg.norm(impact_points - target_2d, axis=1)
    return float(np.percentile(radial_distances, 50))
