import chess
from random import choice
from detector import Detector
from tracker import Tracker

class ChessController:
	detector: Detector
	tracker: Tracker
	
	def __init__(self):
		self.detector = Detector()
		self.tracker = Tracker()

	def get_current_board(self, img):
		piece_positions = self.detector.detect_piece_positions(img)
		return self.tracker.generate_board(piece_positions)

	def pick_move(self, board: chess.Board):
		return choice([move for move in board.legal_moves if board.piece_at(move.from_square).piece_type != chess.KNIGHT])

	def make_move(self, img):
		board = self.get_current_board(img)
		move = self.pick_moves(board)
		return move

