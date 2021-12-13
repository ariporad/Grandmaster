from typing import *
import serial
from time import sleep
from enum import Enum, IntEnum, unique
import serial.tools.list_ports

@unique
class Device(Enum):
	# Values are serial numbers
	GANTRY = "85033313237351301221"
	BOARD = "8503331323735140D1D0"

class Arduino:
	device: Device
	serial: serial.Serial
	buffer: List[int] = []

	def __init__(self, device: Device, baudrate=115200):
		found_arduino = False
		for device in serial.tools.list_ports.comports():
			if device.serial_number is not None and device.serial_number.upper() == device.upper():
				found_arduino = True
				self.serial = serial.Serial(device.device, baudrate=baudrate, timeout=0, exclusive=False)
		
		if not found_arduino:
			raise IOError(f"Couldn't find Arduino! (Name: {device})")

		sleep(2)

	def write(self, data: int):
		self.gantry.write(str(data).encode('utf-8'))
		self.serial.flush()
		self.serial.flushInput()
		self.serial.flushOutput()

	def read(self):
		return [int(x) for x in self.serial.read() if int(x) != 0]

class LightMode(IntEnum):
	OFF = 0
	DEFAULT = 1

class Button(IntEnum):
	COMPUTER = 2
	PLAYER = 3
	START = 0
	FUN = 1

class ArduinoManager:
	gantry: Arduino
	primary: Arduino

	buttons: Dict[Button, bool]
	gantry_pos: Tuple[int, int] = (0, 0)
	electromagnet_enabled: bool = False
	handlers: Dict[Button, function] = {}

	def __init__(self):
		self.gantry = Arduino(Device.GANTRY)
		self.board = Arduino(Device.BOARD)
		self.buttons = {button: False for button in Button}

	def on_button_press(self, button: Button, handler: function):
		if button in self.handlers and self.handlers[button] != handler:
			print("WARNING: overriding handler for button:", button)
		self.handlers[button] = handler
	
	def move_gantry(self, x: int, y: int, block: bool=True):
		"""
		File is accepted as an integer for simplicity, and to allow accessing the graveyard: The
		normal files (A-H) are 0-7, respectively, and the graveyard is files 8-9.
		"""
		self.gantry.write(((x + 1) << 4) | (y + 1))
		if block:
			while self.gantry_pos != (x, y):
				self.update()
	
	def set_electromagnet(self, enabled: bool, block: bool=True):
		self.board.write(0b110 if enabled else 0b010)
		if block:
			while self.electromagnet_enabled != enabled:
				self.update()

	def set_light_mode(self, mode: LightMode):
		print("Light Modes Not Implemented, set to:", mode)

	def set_button_light(self, button: Button, enabled: bool, others: Optional[bool]=None):
		self.board.write((int(enabled) << 4) | (button << 2) | 0b01)
		if others is not None:
			for button in (b for b in Button if b != button):
				self.set_button_light(button, others, others=None)

	def update(self):
		for message in self.board.read():
			for button in Button:
				pressed = bool(message & (1 << button))
				self.buttons[button] = pressed
			self.electromagnet_enabled = bool(message & (1 << 4))

		for message in self.gantry.read():
			message = message & 0xFF
			x = (message >> 4) - 1
			y = (message & 0xF) - 1
			self.gantry_pos = (x, y)




