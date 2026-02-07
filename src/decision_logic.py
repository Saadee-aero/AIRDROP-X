from configs import mission_configs as cfg


def evaluate_drop_decision(hit_probability, probability_threshold):
    if hit_probability >= probability_threshold:
        decision = "DROP"
    else:
        decision = "NO DROP"
    return (decision, probability_threshold)


def get_threshold_for_mode(mode_name):
    return cfg.MODE_THRESHOLDS[mode_name]
