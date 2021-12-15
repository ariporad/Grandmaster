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
    """
    Calculate the Euclidian distance between a and b.
    """
    assert len(a) == len(b)
    sum_squares = 0
    for a_item, b_item in zip(a, b):
        sum_squares = (a_item - b_item) ** 2
    return sqrt(sum_squares)

# In this file to avoid circular imports
def print_to_dashboard(*args):
    """
    This function works exactly like the builtin print(), except that it properly routes output to
    the Dashboard if it's running. If not, it invokes normal print.

    You should use this for all logging. You can even import it over built-in print:
    
    ```python3
    from helpers import print_to_dashboard as print
    ```
    """
    dashboard = get_dashboard()
    if dashboard is None:
        print(*args)
    else:
        dashboard.print(*args)

def show_image(img, title="Image:"):
    """
    Display an image to the user. If available, uses iTerm 2's imgcat functionality. [1]
    Otherwise, opens a window using OpenCV.

    This method waits for user input (press enter) to return. For imgcat, it suspends the
    prompt_toolkit application while executing.
    """
    if not has_imgcat:
        cv2.imshow(title, img)
        cv2.waitKey(0)
    else:
        def _show_image():
            print(title)
            imgcat(img)
            input("Press ENTER to continue... ")
        run_in_terminal(_show_image)
        
    