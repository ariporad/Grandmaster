from typing import *
from math import inf, sqrt
from dashboard import get_dashboard

def distance(a: Tuple, b: Tuple):
    assert len(a) == len(b)
    sum_squares = 0
    for a_item, b_item in zip(a, b):
        sum_squares = (a_item - b_item) ** 2
    return sqrt(sum_squares)

# In this file to avoid circular imports
def print_to_dashboard(*args):
    dashboard = get_dashboard()
    if dashboard is None:
        print(*args)
    else:
        dashboard.print(*args)