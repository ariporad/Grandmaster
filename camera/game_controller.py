from typing import *

import chess
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

		found_arduino = False
		for device in serial.tools.list_ports.comports():
			if device.serial_number is not None and device.serial_number.upper() == GANTRY_ARDUINO_SERIAL_NUMBER.upper():
				found_arduino = True
				self.gantry = serial.Serial(device.device, baudrate=115200, timeout=0.5, exclusive=False)
		
		if not found_arduino:
			raise IOError("Couldn't find Arduino!")

	def move_to_square(self, square: chess.Square, block=True):
		x = chess.square_file(square)
		y = chess.square_rank(square)
		print("MOVING TO SQUARE:", x, y, ((x + 1) << 4) | (y + 1))
		self.gantry.write(str((((x + 1) << 4) | (y + 1))).encode('utf-8'))
		self.gantry.flush()
		self.gantry.flushInput()
		self.gantry.flushOutput()
		# self.arduino.move_to_square(*pos)
		print("MOVED")
		if block:
			new_x = -1
			new_y = -1
			while new_x != x or new_y != y:
				for byte in [int(x) for x in self.gantry.read()]:
					new_x = (byte >> 4) - 1
					new_y = (byte & 0xF) - 1
	
	def set_electromagnet(self, enabled: bool, block=True):
		print("SETITNG EMAG:", enabled)
		self.arduino.set_electromagnet(enabled)
		print("SET EMAG:", enabled)
		if block:
			sleep(2)
			# while self.arduino.electromagnet_enabled != enabled:
			# 	print("WAITING EMAG: cur=", self.arduino.electromagnet_enabled, "target=", enabled)
			# 	self.arduino.tick()
			# 	sleep(0.1)

	def tick(self):
		self.arduino.tick()
		# print("TICK:", self.state, self.arduino.buttons)
		for button, pressed in self.arduino.buttons.items():
			if pressed:
				print("Button", button, "status", pressed)
		if self.state == State.HUMAN_TURN:
			self.arduino.set_button_light(Button.FUN, False)
			self.arduino.set_button_light(Button.START, False)
			self.arduino.set_button_light(Button.COMPUTER, False)
			self.arduino.set_button_light(Button.PLAYER, True)
			# Computer button here is just convenient for debugging
			if self.arduino.buttons[Button.PLAYER] or self.arduino.buttons[Button.COMPUTER]:
				print("Player button pressed! My turn now!")
				self.state = State.COMPUTER_TURN
		elif self.state == State.COMPUTER_TURN:
			print("My turn!")
			self.arduino.set_button_light(Button.FUN, False)
			self.arduino.set_button_light(Button.START, False)
			self.arduino.set_button_light(Button.COMPUTER, True)
			self.arduino.set_button_light(Button.PLAYER, False)
			# img = self.camera.capture_frame()
			# move: chess.Move = self.chess.make_move(img)
			move = chess.Move.from_uci("a1b2")
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
		self.tick()
		print("Grandmaster Ready")
		while True:
			self.tick()

if __name__ == '__main__':
	GameController().main()