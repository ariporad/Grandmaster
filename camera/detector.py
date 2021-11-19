from typing import *
from enum import Enum
from collections import defaultdict
from dataclasses import dataclass
import cv2
from helpers import closest_item
from apriltag import detect_apriltag, apriltag



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
    apriltag_family: str

    def __init__(self, apriltag_family='tag36h11'):
        self.apriltag_family = apriltag_family

    def get_tag_type(self, tag_id: int) -> TagType:
        if tag_id < 128:
            return TagType.BOARD
        else:
            return TagType.PIECE

    def calculate_board_dimensions(self, tags: Dict[TagType, Dict[int, Optional[apriltag.Detection]]]):
        # Board corner tracking tags are centered in squares one rank and one
        # form off the edge of the board (α0, I0, α9, I9).
        # Conventionally, chess boards are drawn with white (Rank 1) at the bottom.
        # Tag IDs: I0 (bottom right) = #0, α0 (bottom left) = #1, α9 (top left) = #2, I9 (top right) = #3

        bottom_right_I0 = tags[TagType.BOARD][0]
        # bottom_left_a0 = tags[1]
        top_left_a9 = tags[TagType.BOARD][2]
        # top_right_I9 = tags[3]

        # or bottom_left_a0 is None or top_right_I9 is None:
        if bottom_right_I0 is None or top_left_a9 is None:
            raise ValueError("Couldn't find board corners!")

        return BoardSize(tuple(top_left_a9.center), tuple(bottom_right_I0.center))

    def detect_piece_positions(self, img):
        gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        detections = detect_apriltag(self.apriltag_family, gray)

        tags: Dict[
            TagType,
            Dict[int, Optional[apriltag.Detection]]
        ] = defaultdict(lambda: defaultdict(lambda: None))

        for tag in detections:
            tags[self.get_tag_type(tag.tag_id)][tag.tag_id] = tag

        size = self.calculate_board_dimensions(tags)

        for tag in sorted(tags[TagType.PIECE].values(), key=lambda tag: tag.tag_id):
            x, y = tag.center
            file = closest_item(size.files, x)
            rank = closest_item(size.ranks, y)
            # Currently everything is a pawn, of either color
            yield f"{file}{rank}", "p" if tag.tag_id >= 256 else "P"


if __name__ == '__main__':
    from sys import argv
    img = cv2.imread(argv[1] if len(argv) >= 2 else 'chessboard.png')
    pieces = Detector().detect_piece_positions(img)

    print("Detected Pieces!")
    for location, letter in pieces:
        print(f"{letter} @ {location}")
