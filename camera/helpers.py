from math import inf


def closest(lst, target, key=lambda x: x):
    closest_diff = inf
    closest_item = None

    for item in lst:
        diff = abs(key(item) - target)
        if diff < closest_diff:
            closest_diff = diff
            closest_item = item

    return closest_item
