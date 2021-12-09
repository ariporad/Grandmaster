from typing import *
from serial import Serial
from enum import IntEnum
from time import sleep

class Arduino:
	name: str
	def __init__(self, port, name):
		pass

	def write(self, data: int):
		pass

	def get_messages(self, max=None) -> List[Dict]:
		"""
		Read, parse, and return any pending messages from the serial port.
		"""
		pass

	def parse_message(self, msg: str):
		"""
		Messages from the Arduino are ascii-encoded, key-value pairs.
		Format:
		> KEY:VALUE;KEY:VALUE
		Over the serial connection, they are newline-deliminated.
		Keys may only contain uppercase letters. Values may contain either (but not both):
		a) uppercase letters and underscores, OR
		b) digits 0-9
		"""
		data = {}
		for pair in msg.upper().split(' '):
			key, value = pair.split(':')
			# attempt to convert value to an int
			try:
				value = int(value)
			except ValueError:
				pass # just use the string value
			data[key] = value
		if 'TYPE' not in data:
			print(f"WARNING(Arduino:{self.name}): Illegal message received:", data)
		return data


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

	buttons: Dict[Button, bool]
	gantry_pos: Tuple[int, int] = (0, 0)
	electromagnet_enabled: bool = False

	def __init__(self):
		self.gantry = Arduino('/dev/ttyACM0')
		self.board = Arduino('/dev/ttyACM1')
		self.buttons = {button: False for button in Button}
	
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

	def tick(self):
		for message in self.board.get_messages():
			if message['TYPE'] == 'BUTTON_PRESS':
				self.buttons[Button[message['BUTTON']]] = bool(message['PRESSED'])
			elif message['TYPE'] == 'MAGNET_STATUS':
				self.electromagnet_enabled = bool(message['ENABLED'])
			else:
				print("Got unknown message from board:", message)

		for message in self.gantry.get_messages():
			if message['TYPE'] == 'POSITION':
				self.gantry = (message['X'], message['Y'])
			else:
				print("Got unknown message from gantry:", message)





