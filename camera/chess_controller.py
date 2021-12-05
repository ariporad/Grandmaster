from random import choice
from camera.detector import Detector
from camera.tracker import Tracker

class ChessController:
	detector: Detector
	tracker: Tracker
	
	def __init__(self):
		pass

	def get_current_board(self, img):
		piece_positions = self.detector.detect_piece_positions(img)
		return self.tracker.generate_board(piece_positions)

	def pick_moves(self, board):
		return choice(board.legal_moves)

	def make_move(self, img):
		board = self.get_current_board(img)
		move = self.pick_moves(board)
		return move

