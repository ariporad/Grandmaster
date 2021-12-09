from typing import *

import chess
from time import sleep
from enum import IntEnum, auto
from camera.camera import Camera
from chess_controller import ChessController
from arduino_controller import ArduinoController, Button

class State(IntEnum):
	HUMAN_TURN = auto()
	COMPUTER_TURN = auto()
	ENDED = auto()

class GameController:
	arduino: ArduinoController
	chess: ChessController
	camera: Camera
	state: State = State.HUMAN_TURN

	def __init__(self, camera_calibration='calibration.json'):
		self.camera = Camera(camera_calibration=camera_calibration)
		self.chess = ChessController()
		self.arduino = ArduinoController()

	def move_to_square(self, square: chess.Square, block=True):
		pos = (chess.square_file(square), chess.square_rank(square))
		self.arduino.move_to_square(*pos)
		if block:
			while self.arduino.gantry_pos != pos:
				self.arduino.tick()
				sleep(0.1)
	
	def set_electromagnet(self, enabled: bool, block=True):
		self.arduino.set_electromagnet(enabled)
		if block:
			while self.arduino.electromagnet_enabled != enabled:
				self.arduino.tick()
				sleep(0.1)

	def tick(self):
		self.arduino.tick()
		print(f"TICK({self.state}): buttons={self.arduino.buttons}")
		if self.state == State.HUMAN_TURN:
			if self.arduino.buttons[Button.PLAYER]:
				print("Player button pressed! My turn now!")
				self.state = State.COMPUTER_TURN
		elif self.state == State.COMPUTER_TURN:
			img = self.camera.capture_frame()
			move = self.chess.make_move(img)
			print("Making Move:", move)
			print("DEBUG OVERRIDE: Moving to b2")
			self.move_to_square(chess.B2)
			print("DONE!")


			



	def main(self):
		while True:
			self.tick()