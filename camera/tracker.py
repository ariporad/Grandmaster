from typing import *
from enum import IntEnum
import chess

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

class Tracker:
	def generate_board(self, positions: List[Tuple[str, int]]):
		board = chess.Board(fen=None)

		for location, tag_id in positions:
			board.set_piece_at(chess.parse_square(location), chess.Piece.from_symbol(Piece(tag_id).symbol))
		
		board.turn = chess.BLACK

		return board