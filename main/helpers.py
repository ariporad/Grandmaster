from typing import *
from math import inf, sqrt


def distance(a: Tuple, b: Tuple):
    assert len(a) == len(b)
    sum_squares = 0
    for a_item, b_item in zip(a, b):
        sum_squares = (a_item - b_item) ** 2
    return sqrt(sum_squares)
