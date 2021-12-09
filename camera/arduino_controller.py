from typing import *
from serial import Serial
from enum import IntEnum

class Arduino:
	def __init__(self, port):
		pass

	def write(self, data: int):
		pass

class LightMode(IntEnum):
	OFF = 0
	DEFAULT = 1

class Button(IntEnum):
	COMPUTER = 0
	PLAYER = 1
	START = 2
	FUN = 3

class ArduinoController:
	gantry: Arduino
	primary: Arduino

	def __init__(self):
		self.gantry = Arduino('TODO')
		self.board = Arduino('TODO')
	
	def move_to_square(self, rank: int, file: int):
		"""
		File is accepted as an integer for simplicity, and to allow accessing the graveyard: The
		normal files (A-H) are 0-7, respectively, and the graveyard is files 8-9.
		"""
		self.gantry.write((file << 2) | rank)
	
	def set_electromagnet(self, enabled: bool):
		self.board.write(0b110 if enabled else 0b010)

	def set_light_mode(self, mode: LightMode):
		print("Light Modes Not Implemented, set to:", mode)

	def set_button_light(self, button: Button, enabled: bool):
		self.board.write((int(enabled) << 4) | (button << 2) | 0b01)
	
	def get_button_presses(self):
		return [] # TODO: return queue of pending button presses


