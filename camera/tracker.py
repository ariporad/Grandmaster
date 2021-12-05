from typing import *
from enum import IntEnum
import chess

# Chess notation doesn't differentiate between identical pieces
# (ex. two black rooks) because it doesn't matter for the game,
# but we want to track individual physical pieces.

# (name, symbol, april tag ID)
PIECES = [
	('WHITE_ROOK_QS',   'R', 100),
	('WHITE_KNIGHT_QS', 'N', 101),
	('WHITE_BISHOP_QS', 'B', 102), # dark squares only
	('WHITE_QUEEN',     'Q', 103),
	('WHITE_KING',      'K', 104),
	('WHITE_BISHOP_KS', 'B', 105), # light squares only
	('WHITE_KNIGHT_KS', 'N', 106),
	('WHITE_ROOK_KS',   'R', 107),
	('WHITE_PAWN_A',    'P', 108),
	('WHITE_PAWN_B',    'P', 109),
	('WHITE_PAWN_C',    'P', 110),
	('WHITE_PAWN_D',    'P', 111),
	('WHITE_PAWN_E',    'P', 112),
	('WHITE_PAWN_F',    'P', 113),
	('WHITE_PAWN_G',    'P', 114),
	('WHITE_PAWN_H',    'P', 115),

	('BLACK_ROOK_QS',   'r', 200),
	('BLACK_KNIGHT_QS', 'n', 201),
	('BLACK_BISHOP_QS', 'b', 202), # dark squares only
	('BLACK_QUEEN',     'q', 203),
	('BLACK_KING',      'k', 204),
	('BLACK_BISHOP_KS', 'b', 205), # light squares only
	('BLACK_KNIGHT_KS', 'n', 206),
	('BLACK_ROOK_KS',   'r', 207),
	('BLACK_PAWN_A',    'p', 208),
	('BLACK_PAWN_B',    'p', 209),
	('BLACK_PAWN_C',    'p', 210),
	('BLACK_PAWN_D',    'p', 211),
	('BLACK_PAWN_E',    'p', 212),
	('BLACK_PAWN_F',    'p', 213),
	('BLACK_PAWN_G',    'p', 214),
	('BLACK_PAWN_H',    'p', 215)
]

Piece = IntEnum('Piece', ((name, tag_id) for name, _, tag_id in PIECES))

symbols_for_piece = {(Piece[name]): symbol for name, symbol, _ in PIECES}

Piece.symbol = property(lambda self: symbols_for_piece[self])

class Tracker:
	def generate_board(self, positions: List[Tuple[str, int]]):
		board = chess.Board(fen=None)

		for location, tag_id in positions:
			board.set_piece_at(chess.parse_square(location), chess.Piece.from_symbol(Piece(tag_id).symbol))

		return board