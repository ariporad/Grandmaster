from typing import *
import serial
from time import sleep
from enum import IntEnum
import serial.tools.list_ports

GANTRY_ARDUINO_SERIAL_NUMBER = "85033313237351301221"
BOARD_ARDUINO_SERIAL_NUMBER = "8503331323735140D1D0"

class Arduino:
	name: str
	serial: serial.Serial
	buffer: List[int] = []

	def __init__(self, name: str, serial_number: str,  baudrate=115200):
		self.name = name.upper()
		
		found_arduino = False
		for device in serial.tools.list_ports.comports():
			if device.serial_number is not None and device.serial_number.upper() == serial_number.upper():
				found_arduino = True
				self.serial = serial.Serial(device.device, baudrate=baudrate, timeout=0.5, exclusive=False)
		
		if not found_arduino:
			raise IOError(f"Couldn't find Arduino! (Name: {name}, SN: {serial_number})")

		sleep(2)

	def write(self, data: int):
		if self.name == 'GANTRY':
			print("Writing to:", self.name, ":", bytes(str(data), 'utf-8'))
		self.serial.write(bytes(str(data) + '\n', 'utf-8'))
		self.serial.flush()
		self.serial.flushInput()
		self.serial.flushOutput()

	def read(self):
		return [int(x) for x in self.serial.read() if int(x) != 0]

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
		self.gantry = Arduino("GANTRY", GANTRY_ARDUINO_SERIAL_NUMBER)
		self.board = Arduino("BOARD", BOARD_ARDUINO_SERIAL_NUMBER)
		self.buttons = {button: False for button in Button}
	
	def move_to_square(self, rank: int, file: int):
		"""
		File is accepted as an integer for simplicity, and to allow accessing the graveyard: The
		normal files (A-H) are 0-7, respectively, and the graveyard is files 8-9.
		"""
		self.gantry.write(((file + 1) << 4) | (rank + 1))
	
	def set_electromagnet(self, enabled: bool):
		self.board.write(0b110 if enabled else 0b010)

	def set_light_mode(self, mode: LightMode):
		print("Light Modes Not Implemented, set to:", mode)

	def set_button_light(self, button: Button, enabled: bool):
		self.board.write((int(enabled) << 4) | (button << 2) | 0b01)

	def tick(self):
		for message in self.board.read():
			for button in Button:
				self.buttons[button] = bool(message & (1 << button))
			self.electromagnet_enabled = bool(message & (1 << 4))

		for message in self.gantry.read():
			message = message & 0b11111111
			x = (message >> 4) - 1
			y = (message & 0b1111) - 1
			self.gantry_pos = (x, y)





