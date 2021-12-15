from typing import *
from helpers import print_to_dashboard as print
import serial
from time import sleep, time
from enum import Enum, IntEnum, unique
import serial.tools.list_ports

ARDUINO_STARTUP_WAIT = 2
"""
Arduinos reset when a serial connection is established, so we can't use them immediately.

We wait this many seconds before attempting to use an Arduino.
"""

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

	on_ready: Callable
	""" Function to be called once all devices are ready. """

	is_ready: bool = False
	""" We are ready once we've gotten at least one status update from each device. """

	is_gantry_ready: bool = False
	is_board_ready: bool = False

	startup_wait_timeout: int
	"""
	Arduinos reset when a serial connection is established, so we can't use them immediately.

	At creation time, this is set to the time (in seconds since the epoch, same format as time.time())
	at which the Arduinos are safe to use. Currently, this is a 2 second delay (see ARDUINO_STARTUP_WAIT).

	We will never be ready before this time, although we're not guaranteed to be ready at that point.
	"""

	def __init__(self, on_ready: Callable = lambda: None, button_handlers: Dict[Button, Callable] = {}):
		self.gantry = Arduino(Device.GANTRY)
		self.board = Arduino(Device.BOARD)
		self.buttons = {button: False for button in Button}
		self.handlers = button_handlers
		self.on_ready = on_ready
		self.startup_wait_timeout = time() + ARDUINO_STARTUP_WAIT

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
		self._assert_ready()
		self.gantry.write(((x + 1) << 4) | (y + 1))
		if block:
			while self.gantry_pos != (x, y):
				self.update()
	
	def set_electromagnet(self, enabled: bool, block: bool=True):
		"""
		Enable/Disable the electromagnet. If block=True, this method will block until that has been done.
		"""
		self._assert_ready()
		self.board.write(0b110 if enabled else 0b010)
		if block:
			while self.electromagnet_enabled != enabled:
				self.update()

	def set_led_pallete(self, pallete: LEDPallete):
		"""
		Set the LEDs around the board to a specific pallete.
		"""
		self._assert_ready()
		self.board.write((int(pallete) << 2) | 0b11)

	def set_button_light(self, button: Button, enabled: bool, others: Optional[bool]=None):
		"""
		Set the light ring around a button. If other is set to a boolean, all other button LEDs will
		be set to that value.
		"""
		self._assert_ready()
		if others is not None:
			for button in Button:
				self.set_button_light(button, others, others=None)
		self.board.write((int(enabled) << 4) | (button << 2) | 0b01)

	def update(self):
		"""
		Process any pending messages from the Arduinos.

		If any buttons are newly pressed, this will trigger appropriate handlers.
		"""
		# Don't do anything if the Arduinos aren't ready yet.
		if self.startup_wait_timeout > time():
			return

		for message in self.board.read():
			if message == 0: continue
			self.is_board_ready = True
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
			if message == 0: continue
			self.is_gantry_ready = True
			message = message & 0xFF
			x = (message >> 4) - 1
			y = (message & 0xF) - 1
			self.gantry_pos = (x, y)
		
		if self.is_board_ready and self.is_gantry_ready and not self.is_ready:
			self.is_ready = True
			self.on_ready()
			self.on_ready = None
	
	def _assert_ready(self):
		if not self.is_ready:
			raise IOError("Arduinos aren't ready yet!")





