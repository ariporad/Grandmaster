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

	def pick_move(self, board):
		return choice(list(board.legal_moves))

	def make_move(self, img):
		board = self.get_current_board(img)
		move = self.pick_moves(board)
		return move

