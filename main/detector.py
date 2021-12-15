from typing import *
from helpers import print_to_dashboard as print, show_image
from enum import IntEnum
import cv2
import chess
import numpy as np
from math import sqrt
from helpers import distance
from apriltag import detect_apriltags, apriltag

# Chess notation doesn't differentiate between identical pieces
# (ex. two black rooks) because it doesn't matter for the game,
# but we want to track individual physical pieces.

# (name, symbol, april tag ID)
PIECES = [
	('WHITE_ROOK_QS',   'R', 200),
	('WHITE_KNIGHT_QS', 'N', 201),
	('WHITE_BISHOP_QS', 'B', 202), # dark squares only
	('WHITE_QUEEN',     'Q', 203),
	('WHITE_KING',      'K', 204),
	('WHITE_BISHOP_KS', 'B', 205), # light squares only
	('WHITE_KNIGHT_KS', 'N', 206),
	('WHITE_ROOK_KS',   'R', 207),
	('WHITE_PAWN_A',    'P', 208),
	('WHITE_PAWN_B',    'P', 209),
	('WHITE_PAWN_C',    'P', 210),
	('WHITE_PAWN_D',    'P', 211),
	('WHITE_PAWN_E',    'P', 212),
	('WHITE_PAWN_F',    'P', 213),
	('WHITE_PAWN_G',    'P', 214),
	('WHITE_PAWN_H',    'P', 215),

	('BLACK_ROOK_QS',   'r', 100),
	('BLACK_KNIGHT_QS', 'n', 101),
	('BLACK_BISHOP_QS', 'b', 102), # dark squares only
	('BLACK_QUEEN',     'q', 103),
	('BLACK_KING',      'k', 104),
	('BLACK_BISHOP_KS', 'b', 105), # light squares only
	('BLACK_KNIGHT_KS', 'n', 106),
	('BLACK_ROOK_KS',   'r', 107),
	('BLACK_PAWN_A',    'p', 108),
	('BLACK_PAWN_B',    'p', 109),
	('BLACK_PAWN_C',    'p', 110),
	('BLACK_PAWN_D',    'p', 111),
	('BLACK_PAWN_E',    'p', 112),
	('BLACK_PAWN_F',    'p', 113),
	('BLACK_PAWN_G',    'p', 114),
	('BLACK_PAWN_H',    'p', 115)
]

Piece = IntEnum('Piece', ((name, tag_id) for name, _, tag_id in PIECES))

symbols_for_piece = {(Piece[name]): symbol for name, symbol, _ in PIECES}

Piece.symbol = property(lambda self: symbols_for_piece[self])

# All pieces (and only pieces) have Apriltag IDs >= 100
MIN_PIECE_TAG_ID = 100

class Detector:
    """
    This class is responsible for the computer vision pipeline which identifies the location of each
    chess piece in chess-space (ie. ranks and forms) from an image of the board.
    """
    piece_apriltag_family = 'tag36h11'
    corner_apriltag_family = 'tag36h11'

    CORNER_I0_TAG_ID = 2  # bottom right
    CORNER_a0_TAG_ID = 3  # bottom left
    CORNER_a9_TAG_ID = 0  # top left
    CORNER_I9_TAG_ID = 1  # top right

    def detect_board(self, img, turn=chess.BLACK, show=False):
        """
        Generate a Python Chess Board object from an image. Simple wrapper around detect_piece_positions
        and generate_board.
        """
        positions = self.detect_piece_positions(img, show)
        board = self.generate_board(positions, turn=turn)
        return board

    def generate_board(self, positions: List[Tuple[str, int]], turn=chess.BLACK):
        """
        Generate a Python Chess Board object from a list of piece positions.
        """
        board = chess.Board(fen=None)
        
        for location, tag_id in positions:
            board.set_piece_at(chess.parse_square(location), chess.Piece.from_symbol(Piece(tag_id).symbol))

        board.turn = turn

        return board

    def detect_piece_positions(self, img, show=False):
        """
        Run the computer vision pipeline to determine the position of each piece on the board in
        chess-space from a picture of it.

        If show is True, the image will be (destructively) annotated to indicate the detected
        locations of each Apriltag (board or piece) and the calculated position of each square. It
        will then be shown to the user (using helpers.show_image).
        """
        # Apriltags can only be detected on grayscale images
        gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        tags = detect_apriltags(self.corner_apriltag_family, gray)
        squares = self.calculate_square_locations(tags)
        # These are the four squares around the center of the chessboard
        board_center = np.mean([squares['d4'], squares['d5'], squares['e4'], squares['e5']], axis=0)

        if show:
            # Very hack-y code to annotate the image with helpful information
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

            for tag in (tag for tag_id, tag in tags.items() if tag_id >= MIN_PIECE_TAG_ID):
                x = round(tag.center[0])
                y = round(tag.center[1])
                img[y-10:y+11, x-10:x+11, :] = [0, 255, 0]

            for pos in squares.values():
                x = round(pos[0])
                y = round(pos[1])
                img[y-10:y+11, x-10:x+11, :] = [255, 0, 0]
            
            show_image(img)

        # We process piece tags in descending order of distance from the center. This is because our
        # camera has a fisheye lens, and so pieces (especially tall pieces) that are near the edge
        # of the board (ie. a king on a1) might appear farther from the center than they actually are.
        # However, they can't be closer to a different square, so as long as we process them first
        # they'll get assigned to the right square. Then if a piece next to them has the same issue,
        # it will get assigned to the best remaining square which will also be correct.
        for tag in sorted(
            (tag for tag_id, tag in tags.items() if tag_id >= MIN_PIECE_TAG_ID),
            key=lambda tag: distance(board_center, tag.center),
            reverse=True):
            def _key(item):
                _, pos = item
                x, y = pos
                return sqrt(((x - tag.center[0]) ** 2) + ((y - tag.center[1]) ** 2))
            square = sorted(squares.items(), key=_key)[0][0]
            del squares[square]
            yield square, tag.tag_id

    def calculate_square_locations(self, tags: Dict[int, Optional[apriltag.Detection]]) -> Dict[str, np.array]:
        """
        From the board corner Apriltags, infer the location of the center of each square on the
        chess board.

        Returns a mapping of square names (ex. 'c3') to center locations (in pixels).
        """
        # Board corner tracking tags are centered in (imaginary) squares one rank and one form off
        # the edge of the board (α0, I0, α9, I9). This leaves them 9 square widths apart on each axis.
        # Conventionally, chess boards are drawn with white (Rank 1) at the bottom.
        try:
            bottom_right_I0 = np.array(tags[self.CORNER_I0_TAG_ID].center)
            bottom_left_a0  = np.array(tags[self.CORNER_a0_TAG_ID].center)
            top_left_a9     = np.array(tags[self.CORNER_a9_TAG_ID].center)
            top_right_I9    = np.array(tags[self.CORNER_I9_TAG_ID].center)
        except:
            raise ValueError("Couldn't find board corners!")

        # This algorithm isn't precisely methodologically sound, but it's a good heuristic and close
        # enough for our purposes. It's complicated by the fact that the camera won't be perfectly
        # aligned with the board (both in the sense that the plane of the camera won't be parallel
        # to the plane of the board, and that the y-axis of the camera won't be parallel to the
        # y-axis of the board).
        #
        # Essentially, we calculate distance (along both the x- and y-axis) between each pair of
        # corner tags (ie. left edge, top edge, right edge, bottom edge). Taking the left edge as an
        # example, we take the difference between the bottom left and top right corner square, and
        # assume that the squares of the A-file (various ranks) are evenly spaced throughout that range.
        # 
        # That would handle the y-axis of the camera not being aligned with the y-axis of the board,
        # but doesn't address the misaligned planes. To account for that we also calculate the
        # difference between the top _right_ and bottom _right_ corners. If the planes of the camera
        # and board were perfectly parallel, the left edge and the right edge would be the same.
        # Instead, we assume the difference between the two is linearly distributed across the image.
        # (So if the left edge is fewer pixels long than the right edge, the ranks of the A-file are
        # slightly closer together than the ranks of the B-file, and so on.) We do the samething for
        # each rank.
        #
        # Except, we don't: in some practical testing, the best result was given by only doing the
        # second-order correction for ranks (the amount that the distance between each rank changes
        # with each file) and not for files, so we do that. Again, this is a theoretically-wrong
        # heuristic that works pretty well in practice.
        
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
                # Solution: methodologically wrong, good enough
                pos = origin + \
                    rank_i * (d_rank_a + (1 * d_rank_d_file * file_i)) + \
                    file_i * (d_file_0 + (0 * d_file_d_rank * rank_i))

                squares[file + rank] = pos
        
        return squares
