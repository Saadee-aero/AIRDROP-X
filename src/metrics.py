import numpy as np


def compute_hit_probability(impact_points, target_position, target_radius):
    impact_points = np.asarray(impact_points, dtype=float)
    target_position = np.asarray(target_position, dtype=float)
    if impact_points.shape[0] == 0:
        raise ValueError("impact_points must not be empty")
    if impact_points.shape[1] != 2:
        raise ValueError("impact_points must have shape (N, 2)")
    target_2d = target_position.reshape(2)
    radial_distances = np.linalg.norm(impact_points - target_2d, axis=1)
    hits = np.sum(radial_distances <= target_radius)
    return float(hits / impact_points.shape[0])


def compute_cep50(impact_points, target_position):
    impact_points = np.asarray(impact_points, dtype=float)
    target_position = np.asarray(target_position, dtype=float)
    if impact_points.shape[0] == 0:
        raise ValueError("impact_points must not be empty")
    if impact_points.shape[1] != 2:
        raise ValueError("impact_points must have shape (N, 2)")
    target_2d = target_position.reshape(2)
    radial_distances = np.linalg.norm(impact_points - target_2d, axis=1)
    return float(np.percentile(radial_distances, 50))
