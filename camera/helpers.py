from math import inf


def closest_item(dict, target):
    closest_diff = inf
    closest_key = None

    for key, value in dict.items():
        diff = abs(value - target)
        if diff < closest_diff:
            closest_diff = diff
            closest_key = key

    return closest_key
