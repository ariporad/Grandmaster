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
			self.arduino.set_button_light(Button.FUN, False)
			self.arduino.set_button_light(Button.START, False)
			self.arduino.set_button_light(Button.COMPUTER, False)
			self.arduino.set_button_light(Button.PLAYER, True)
			if self.arduino.buttons[Button.PLAYER]:
				print("Player button pressed! My turn now!")
				self.state = State.COMPUTER_TURN
		elif self.state == State.COMPUTER_TURN:
			self.arduino.set_button_light(Button.FUN, False)
			self.arduino.set_button_light(Button.START, False)
			self.arduino.set_button_light(Button.COMPUTER, True)
			self.arduino.set_button_light(Button.PLAYER, False)
			img = self.camera.capture_frame()
			move: chess.Move = self.chess.make_move(img)
			print("Making Move:", move)

			self.set_electromagnet(False)
			self.move_to_square(move.from_square)
			self.set_electromagnet(True)
			self.move_to_square(move.to_square)
			self.set_electromagnet(False)

			print("DONE! It's the human's turn now!")
			self.state = State.HUMAN_TURN
			self.arduino.set_button_light(Button.COMPUTER, False)
			self.arduino.set_button_light(Button.PLAYER, True)
		else:
			print("Unknown State:", self.state)
			self.arduino.set_button_light(Button.FUN, True)
			self.arduino.set_button_light(Button.START, True)
			self.arduino.set_button_light(Button.COMPUTER, False)
			self.arduino.set_button_light(Button.PLAYER, False)

	def main(self):
		while True:
			self.tick()

if __name__ == '__main__':
	GameController().main()