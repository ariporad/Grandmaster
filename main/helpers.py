import cv2
from typing import *
from math import inf, sqrt
from dashboard import get_dashboard
from prompt_toolkit.application import run_in_terminal

has_imgcat = False
try:
	from imgcat import imgcat
	has_imgcat = True
except ImportError:
	pass

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

def show_image(img):
    if not has_imgcat:
        cv2.imshow(img)
        cv2.waitKey(0)
    else:
        def _show_image():
            imgcat(img)
            input("Press ENTER to continue... ")
        run_in_terminal(_show_image)
        
    