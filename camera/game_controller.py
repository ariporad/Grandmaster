from typing import *

import cv2
import chess
import requests
import numpy as np
import serial
import serial.tools.list_ports
from time import sleep
from enum import IntEnum, auto
from cam import Camera
from chess_controller import ChessController
from arduino_controller import ArduinoController, Button

class State(IntEnum):
	HUMAN_TURN = 0
	COMPUTER_TURN = 1
	ENDED = 2

GANTRY_ARDUINO_SERIAL_NUMBER = "85033313237351301221"

class GameController:
	arduino: ArduinoController
	chess: ChessController
	camera: Camera
	state: State = State.HUMAN_TURN
	gantry: serial.Serial

	def __init__(self, calibration_file='calibration.json'):
		self.camera = Camera(calibration_file=calibration_file)
		self.chess = ChessController()
		self.arduino = ArduinoController()

	def move_to_square(self, square: chess.Square, block=True):
		x = chess.square_file(square)
		y = chess.square_rank(square)
		print("MOVING TO SQUARE:", chess.square_name(square), x, y)
		self.arduino.move_to_square(x, y, block)
		print("MOVED")
	
	def set_electromagnet(self, enabled: bool, block=True):
		print("SETITNG EMAG:", enabled)
		self.arduino.set_electromagnet(enabled, block)
		print("SET EMAG:", enabled)
	
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

	def tick(self):
		self.arduino.tick()
		for button, pressed in self.arduino.buttons.items():
			if pressed:
				print("Button", button, "status", pressed)
		if self.state == State.HUMAN_TURN:
			self.arduino.set_button_light(Button.PLAYER, True, others=False)
			# Computer button here is just convenient for debugging
			if self.arduino.buttons[Button.PLAYER] or self.arduino.buttons[Button.COMPUTER]:
				print("Player button pressed! My turn now!")
				self.state = State.COMPUTER_TURN
		elif self.state == State.COMPUTER_TURN:
			print("My turn!")
			self.arduino.set_button_light(Button.COMPUTER, True, others=False)
			print("Fetching image...")
			img = self.get_image() #self.camera.capture_frame()
			print("Got image!")
			cv2.imshow("Fetched image", img)
			# cv2.waitKey(0)
			# cv2.destroyAllWindows()
			board: chess.Board = self.chess.get_current_board(img)
			print("Got Board:")
			print(board)
			move: chess.Move = self.chess.pick_move(board)
			# move = chess.Move.from_uci("a1b2")
			print("Making Move:", move)

			self.set_electromagnet(False)
			self.move_to_square(move.from_square)
			self.set_electromagnet(True)
			self.move_to_square(move.to_square)
			self.set_electromagnet(False)

			print("DONE! It's the human's turn now!")
			self.state = State.HUMAN_TURN
			self.arduino.set_button_light(Button.PLAYER, True, others=False)
		else:
			print("Unknown State:", self.state)
			self.arduino.set_button_light(Button.FUN, True, others=False)

	def main(self):
		self.tick()
		print("Grandmaster Ready")
		while True:
			self.tick()

if __name__ == '__main__':
	GameController().main()