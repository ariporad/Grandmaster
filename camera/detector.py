from typing import *
from enum import Enum
from collections import defaultdict
from dataclasses import dataclass
import cv2
from helpers import closest_item
from apriltag import detect_apriltags, apriltag



class TagType(Enum):
    BOARD = 'BOARD'
    PIECE = 'PIECE'


@dataclass
class BoardSize:
    top_left: Tuple[float, float]
    bottom_right: Tuple[float, float]

    @property
    def board_size(self):
        """
        NOTE: These sizes may be negative in the board is upside-down
        """
        return (
            self.bottom_right[0] - self.top_left[0],
            self.bottom_right[1] - self.top_left[1]
        )

    @property
    def square_size(self):
        return (self.board_size[0] / 9, self.board_size[1] / 9)

    # Ranks and Files are both dicts mapping letters/numbers to center positions
    @property
    def ranks(self):
        ranks = {}
        for num in range(1, 9):
            ranks[num] = self.bottom_right[1] - (self.square_size[1] * num)
        return ranks

    @property
    def files(self):
        files = {}
        for num, letter in enumerate('abcdefgh', start=1):
            files[letter] = self.top_left[0] + (self.square_size[0] * num)
        return files

#
# Read Image & Run Detector
#


class Detector:
    piece_apriltag_family = 'tag36h11'
    corner_apriltag_family = 'tag36h11'

    CORNER_I0_TAG_ID = 0  # bottom right
    CORNER_a0_TAG_ID = 1  # bottom left
    CORNER_a9_TAG_ID = 2  # top left
    CORNER_I9_TAG_ID = 3  # top right

    def get_tag_type(self, tag_id: int) -> TagType:
        if tag_id < 128:
            return TagType.BOARD
        else:
            return TagType.PIECE

    def calculate_board_dimensions(self, tags: Dict[int, Optional[apriltag.Detection]]):
        # Board corner tracking tags are centered in squares one rank and one
        # form off the edge of the board (α0, I0, α9, I9).
        # Conventionally, chess boards are drawn with white (Rank 1) at the bottom.

        bottom_right_I0 = tags[self.CORNER_I0_TAG_ID]
        # bottom_left_a0 = tags[1]
        top_left_a9 = tags[self.CORNER_a9_TAG_ID]
        # top_right_I9 = tags[3]

        # or bottom_left_a0 is None or top_right_I9 is None:
        if bottom_right_I0 is None or top_left_a9 is None:
            raise ValueError("Couldn't find board corners!")

        return BoardSize(tuple(top_left_a9.center), tuple(bottom_right_I0.center))

    def detect_piece_positions(self, img):
        gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        tags = detect_apriltags(self.corner_apriltag_family, gray)

        top_left     = tags[self.CORNER_a9_TAG_ID].center
        top_right    = tags[self.CORNER_I9_TAG_ID].center
        bottom_left  = tags[self.CORNER_a0_TAG_ID].center
        bottom_right = tags[self.CORNER_I0_TAG_ID].center

        # If the image is perfectly aligned all of these will be zero
        dx_left = top_left[0] - bottom_left[0]
        dx_right = top_right[0] - bottom_right[0]
        dy_top = top_left[1] - top_right[1]
        dy_bottom = bottom_left[1] - bottom_right[1]

        dx_mean = (dx_left + dx_right) / 2
        dy_mean = (dy_top + dy_bottom) / 2

        size = self.calculate_board_dimensions(tags)

        for tag in sorted((tag for tag_id, tag in tags.items() if tag_id >= 128), key=lambda tag: tag.tag_id):
            x, y = tag.center
            file = closest_item(size.files, x)
            rank = closest_item(size.ranks, y)
            yield f"{file}{rank}", tag.tag_id

if __name__ == '__main__':
    from sys import argv
    img = cv2.imread(argv[1] if len(argv) >= 2 else 'chessboard.png')
    pieces = Detector().detect_piece_positions(img)

    print("Detected Pieces!")
    for location, letter in pieces:
        print(f"{letter} @ {location}")
