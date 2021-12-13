from typing import *
from math import inf, sqrt


def closest_item(items: dict, target, distance=lambda value, target: abs(value - target)):
    closest_diff = inf
    closest_key = None

    for key, value in items.items():
        diff = distance(value, target)
        if diff < closest_diff:
            closest_diff = diff
            closest_key = key

    return closest_key

def distance(a: Tuple, b: Tuple):
    assert len(a) == len(b)
    sum_squares = 0
    for a_item, b_item in zip(a, b):
        sum_squares = (a_item - b_item) ** 2
    return sqrt(sum_squares)
