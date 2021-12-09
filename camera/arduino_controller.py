from typing import *
from serial import Serial
from enum import IntEnum

class Arduino:
	def __init__(self, port):
		pass

	def write(self, data):
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
		self.primary = Arduino('TODO')
	
	def move_to_square(self, square: int):
		pass
	
	def set_electromagnet(self, enabled: bool):
		pass

	def set_light_mode(self, mode: LightMode):
		pass

	def set_button_light(self, button: Button, enabled: bool):
		pass
	
	def get_button_presses(self):
		return [] # TODO: return queue of pending button presses


