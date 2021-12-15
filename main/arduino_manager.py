from typing import *
from helpers import print_to_dashboard as print
import serial
from time import sleep
from enum import Enum, IntEnum, unique
import serial.tools.list_ports

@unique
class Device(Enum):
	"""
	An enum to keep track of the different Arduinos that we use.
	Values are the Arduino's serial number, which is used to identify and connect to it.
	"""
	GANTRY = "85033313237351301221"
	BOARD = "8503331323735140D1D0"

class Arduino:
	device: Device
	serial: serial.Serial
	buffer: List[int] = []

	def __init__(self, device: Device, baudrate=115200):
		"""
		Connect to an Arduino.
		"""
		for d in serial.tools.list_ports.comports():
			if d.serial_number is not None and d.serial_number.upper() == device.value.upper():
				self.serial = serial.Serial(d.device, baudrate=baudrate, timeout=0, exclusive=False)
				break
		else:
			raise IOError(f"Couldn't find Arduino! ({device})")

		# Arduinos reset on connection, so give it a minute to boot up
		sleep(5)

	def write(self, data: int):
		"""
		Write data to the Arduino.
		"""
		self.serial.write((str(data) + '\n').encode('utf-8'))
		# I spent _weeks_ debugging the weirdest serial communication errors: especially on the
		# Raspberry Pi, there would be dozens of seconds of delay when sending anything and the
		# data would be corrupted (ie. only some bytes get there, etc.)
		#
		# Calling all three flush methods felt stupid, but seemed to improve the situation slightly.
		# Switching to a Macbook Pro helped tremendously.
		#
		# However, on the last day of the project the issue came back, and I discovered (I think)
		# that the real problem was multithreading: I think PySerial does its sending/receiving on a
		# different thread, and so was being blocked. Adding a sleep(0) (ie. a thread yield) seemed
		# to solve the problem. This would also make sense with why it was more pronounced on the
		# (single-core) Raspberry Pi.
		self.serial.flush()
		self.serial.flushInput()
		self.serial.flushOutput()
		sleep(0)

	def read(self):
		sleep(0) # see above
		return [int(x) for x in self.serial.read() if int(x) != 0]

# Keep in sync with board.ino:led_set_pallete
class LEDPallete(IntEnum):
	"""
	List of possible LED modes (palletes) for the LEDs around the edge of the board.
	"""
	FAIL = 0
	BOOTUP = 1
	GETTING_READY = 2
	READY = 3
	HUMAN_TURN = 4
	AUTOPLAY_HUMAN_THINK = 5
	COMPUTER_MOVE = 6
	COMPUTER_THINK = 7

class Button(IntEnum):
	"""
	Physical buttons.
	"""
	COMPUTER = 2
	PLAYER = 3
	START = 0
	FUN = 1

class ArduinoManager:
	"""
	This class is responsible for encapsulating all communication with the Arduino, including
	encapsulating the distinction between the two Arduinos.
	"""
	gantry: Arduino
	primary: Arduino

	buttons: Dict[Button, bool]
	""" Most recent known state of each button. """

	gantry_pos: Tuple[int, int] = (0, 0)
	""" Most recent known position of the gantry. """

	electromagnet_enabled: bool = False
	""" Status of the electromagnet. """

	handlers: Dict[Button, Callable]
	""" Mapping of handlers to be invoked when a button becomes pressed. """

	def __init__(self, button_handlers: Dict[Button, Callable] = {}):
		self.gantry = Arduino(Device.GANTRY)
		self.board = Arduino(Device.BOARD)
		self.buttons = {button: False for button in Button}
		self.handlers = button_handlers

	def on_button_press(self, button: Button, handler: Callable):
		"""
		Register a handler for when a button is pressed. This will replace (with a warning) any
		previous handler for that button.
		"""
		if button in self.handlers and self.handlers[button] != handler:
			print("WARNING: overriding handler for button:", button)
		self.handlers[button] = handler
	
	def move_gantry(self, x: int, y: int, block: bool=True):
		"""
		Move the gantry to a specific position. If block=True, this method will block until the
		gantry is in place.

		File is accepted as an integer for simplicity, and to allow accessing the graveyard: The
		normal files (A-H) are 0-7, respectively, and the graveyard is files 8-9.
		"""
		self.gantry.write(((x + 1) << 4) | (y + 1))
		if block:
			while self.gantry_pos != (x, y):
				self.update()
	
	def set_electromagnet(self, enabled: bool, block: bool=True):
		"""
		Enable/Disable the electromagnet. If block=True, this method will block until that has been done.
		"""
		self.board.write(0b110 if enabled else 0b010)
		if block:
			while self.electromagnet_enabled != enabled:
				self.update()

	def set_led_pallete(self, pallete: LEDPallete):
		"""
		Set the LEDs around the board to a specific pallete.
		"""
		self.board.write((int(pallete) << 2) | 0b11)

	def set_button_light(self, button: Button, enabled: bool, others: Optional[bool]=None):
		"""
		Set the light ring around a button. If other is set to a boolean, all other button LEDs will
		be set to that value.
		"""
		self.board.write((int(enabled) << 4) | (button << 2) | 0b01)
		if others is not None:
			for button in (b for b in Button if b != button):
				self.set_button_light(button, others, others=None)

	def update(self):
		"""
		Process any pending messages from the Arduinos.

		If any buttons are newly pressed, this will trigger appropriate handlers.
		"""
		for message in self.board.read():
			for button in Button:
				pressed = bool(message & (1 << button))
				change = pressed != self.buttons[button]
				self.buttons[button] = pressed
				if change:
					print(button, 'is', 'pressed' if pressed else 'unpressed')
					if button in self.handlers:
						self.handlers[button]()

			self.electromagnet_enabled = bool(message & (1 << 4))

		for message in self.gantry.read():
			message = message & 0xFF
			x = (message >> 4) - 1
			y = (message & 0xF) - 1
			self.gantry_pos = (x, y)





