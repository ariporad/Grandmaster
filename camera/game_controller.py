from typing import *

import cv2
import chess
import requests
import numpy as np
import serial
import serial.tools.list_ports
from time import sleep
from enum import IntEnum
from cam import Camera
from random import choice
from tracker import Tracker
from detector import Detector
from arduino_controller import ArduinoController, Button

class State(IntEnum):
	HUMAN_TURN = 0
	COMPUTER_TURN = 1
	ENDED = 2

GANTRY_ARDUINO_SERIAL_NUMBER = "85033313237351301221"

class GameController:
	arduino: ArduinoController
	camera: Camera
	state: State = State.HUMAN_TURN
	gantry: serial.Serial

	def __init__(self, calibration_file='calibration.json'):
		self.camera = Camera(calibration_file=calibration_file)
		self.detector = Detector()
		self.tracker = Tracker()
		self.arduino = ArduinoController()
		self.arduino.on_button_press(Button.PLAYER, self.play_computer_turn)

	def play_computer_turn(self):
		if self.state != State.HUMAN_TURN: return
		
		print("My turn!")
		self.state = State.COMPUTER_TURN
		self.arduino.set_button_light(Button.COMPUTER, True, others=False)

		print("Fetching image...")
		img = self.get_image()
		print("Got image!")

		cv2.imshow("Fetched image", img)
		# cv2.waitKey(0)
		# cv2.destroyAllWindows()

		piece_positions = self.detector.detect_piece_positions(img)
		board = self.tracker.generate_board(piece_positions)
		print("Got Board:")
		print(board)
		move: chess.Move = self.pick_move(board)
		# move = chess.Move.from_uci("a1b2")
		print("Making Move:", move)

		self.arduino.set_electromagnet(False)
		self.move_to_square(move.from_square)
		self.arduino.set_electromagnet(True)
		self.move_to_square(move.to_square)
		self.arduino.set_electromagnet(False)

		print("DONE! It's the human's turn now!")
		self.start_human_turn()
	
	def pick_move(self, board: chess.Board):
		return choice([move for move in board.legal_moves if board.piece_at(move.from_square).piece_type != chess.KNIGHT])

	def start_human_turn(self):
		self.state = State.HUMAN_TURN
		self.arduino.set_button_light(Button.PLAYER, True, others=False)

	def move_to_square(self, square: chess.Square, block=True):
		x = chess.square_file(square)
		y = chess.square_rank(square)
		self.arduino.move_gantry(x, y, block)
	
	def get_image(self, retry=5):
		try:
			r = requests.get('http://192.168.34.100:5555/camera.png', stream=True).raw
			# r = requests.get('http://grandmaster.local:5555/camera.png')
			return cv2.imdecode(np.asarray(bytearray(r.read()), dtype='uint8'), cv2.IMREAD_COLOR)
		except Exception as err:
			if retry > 0:
				print(f"Failed to fetch image, retrying {retry} more times in 3 seconds!", err)
				sleep(3)
				return self.get_image(retry - 1)
			else:
				raise

	def main(self):
		self.arduino.tick()
		print("Grandmaster Ready")
		self.start_human_turn()
		while True:
			self.arduino.tick()

if __name__ == '__main__':
	GameController().main()