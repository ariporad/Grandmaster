from typing import *
from enum import Enum
from collections import defaultdict
from dataclasses import dataclass
import cv2
import chess
import numpy as np
from math import sqrt
from helpers import closest_item, distance
from apriltag import detect_apriltags, apriltag



class TagType(Enum):
    BOARD = 'BOARD'
    PIECE = 'PIECE'

#
# Read Image & Run Detector
#


class Detector:
    piece_apriltag_family = 'tag36h11'
    corner_apriltag_family = 'tag36h11'

    CORNER_I0_TAG_ID = 2  # bottom right
    CORNER_a0_TAG_ID = 3  # bottom left
    CORNER_a9_TAG_ID = 0  # top left
    CORNER_I9_TAG_ID = 1  # top right

    def get_tag_type(self, tag_id: int) -> TagType:
        if tag_id < 128:
            return TagType.BOARD
        else:
            return TagType.PIECE

    def calculate_board_dimensions(self, tags: Dict[int, Optional[apriltag.Detection]]):
        # Board corner tracking tags are centered in squares one rank and one
        # form off the edge of the board (α0, I0, α9, I9).
        # Conventionally, chess boards are drawn with white (Rank 1) at the bottom.

        print("GENERATING SQUARES:")

        try:
            bottom_right_I0 = np.array(tags[self.CORNER_I0_TAG_ID].center)
            bottom_left_a0  = np.array(tags[self.CORNER_a0_TAG_ID].center)
            top_left_a9     = np.array(tags[self.CORNER_a9_TAG_ID].center)
            top_right_I9    = np.array(tags[self.CORNER_I9_TAG_ID].center)
            print("TL a9:", np.rint(top_left_a9))
            print("TR I9:", np.rint(top_right_I9))
            print("BL a0:", np.rint(bottom_left_a0))
            print("BR I0:", np.rint(bottom_right_I0))
        except:
            raise ValueError("Couldn't find board corners!")
        
        # Divide by 9 because there are 9 squares between each corner tag
        origin = bottom_left_a0 # a0 is the origin

        d_rank_a = (top_left_a9 - bottom_left_a0) / 9
        d_rank_I = (top_right_I9 - bottom_right_I0) / 9

        d_file_0 = (bottom_right_I0 - bottom_left_a0) / 9
        d_file_9 = (top_right_I9 - top_left_a9) / 9

        d_rank_d_file = (d_rank_I - d_rank_a) / 9 # for every file, d_rank changes by this
        d_file_d_rank = (d_file_9 - d_file_0) / 9 # for every rank, d_file changes by this

        squares = {}

        for rank_i, rank in enumerate(chess.RANK_NAMES, start=1):
            for file_i, file in enumerate(chess.FILE_NAMES, start=1):
                # This methodology for generating square center positions is not methodologically
                # sound, but it's good enough. Other attempts kept for posterity. 
                
                # Solution: methodologically wrong, good enough
                pos = origin + \
                    rank_i * (d_rank_a + (1 * d_rank_d_file * file_i)) + \
                    file_i * (d_file_0 + (0 * d_file_d_rank * rank_i))

                # Cumulative d_rank_d_file adjustment
                # pos = origin + \
                #     (rank_i * d_rank_a) + (d_rank_d_file * (sum(range((0 + file_i))) - 0)) + \
                #     (file_i * d_file_0) #+ (d_file_d_rank * (sum(range((0 + rank_i))) - 0))

                # Only count straight distance from origin
                # adjustment = ((file_i ** 2) + (rank_i ** 2)) * np.abs(d_rank_d_file)
                # pos = origin + \
                #     rank_i * d_rank_a + \
                #     file_i * d_file_0 + \
                #     adjustment

                squares[file + rank] = pos
        
        return squares

    def detect_piece_positions(self, img, show=False):
        gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        tags = detect_apriltags(self.corner_apriltag_family, gray)
        squares = self.calculate_board_dimensions(tags)
        board_center = np.mean([squares['d4'], squares['d5'], squares['e4'], squares['e5']], axis=0)

        if show:
            # Very kludge-y code to mark the apriltags
            bottom_right_I0 = tags[self.CORNER_I0_TAG_ID].center
            bottom_left_a0 = tags[self.CORNER_a0_TAG_ID].center
            top_left_a9 = tags[self.CORNER_a9_TAG_ID].center
            top_right_I9 = tags[self.CORNER_I9_TAG_ID].center

            for tag in [bottom_left_a0, bottom_right_I0, top_left_a9, top_right_I9, board_center]:
                x = round(tag[0])
                y = round(tag[1])
                color = [0, 0, 255]
                # Make the origin a different color
                if np.array_equal(tag, bottom_left_a0):
                    color = [0, 255, 255]
                elif np.array_equal(tag, board_center):
                    color = [255, 0, 255]
                img[y-10:y+11, x-10:x+11, :] = color

            for tag in sorted((tag for tag_id, tag in tags.items() if tag_id >= 128), key=lambda tag: tag.tag_id):
                x = round(tag.center[0])
                y = round(tag.center[1])
                img[y-10:y+11, x-10:x+11, :] = [0, 255, 0]

            for pos in squares.values():
                x = round(pos[0])
                y = round(pos[1])
                img[y-10:y+11, x-10:x+11, :] = [255, 0, 0]
            
            cv2.imshow("Squares", img)
            cv2.waitKey(0)
        
        for tag in sorted((tag for tag_id, tag in tags.items() if tag_id >= 128), key=lambda tag: tag.tag_id):
            square = closest_item(squares, tag.center, distance=distance)
            del squares[square]
            yield square, tag.tag_id

if __name__ == '__main__':
    from sys import argv
    img = cv2.imread(argv[1] if len(argv) >= 2 else 'chessboard.png')
    pieces = Detector().detect_piece_positions(img, show=True)

    print("Detected Pieces!")
    for location, letter in pieces:
        print(f"{letter} @ {location}")
    
    cv2.destroyAllWindows()
