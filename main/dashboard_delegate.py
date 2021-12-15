"""
The dashboard delegate has two functions:

First, it encapsulates all GameController-related dashboard logic to avoid a circular
Dashboard -> GameController -> Dashboard dependency (due to logging).

Second, the dashboard delegate (specifically, DashboardDelegateThread) runs the entire GameController
on a background thread and handles thread-safe communication. This is nessecary because the
Dashboard UI (through prompt_toolkit) uses an asyncio event loop for non-blocking IO while the
GameController (through PySerial) uses almost-exclusively blocking IO. Moving the GameController to
a separate thread was far easier than re-writing it to use asyncio.
"""
from collections import deque
from typing import *
from sys import exit
import chess
from threading import Thread, Lock
from game_controller import GameController
from arduino_manager import Button, LEDPallete
from helpers import print_to_dashboard as print, show_image

class DashboardDelegate:
	"""
	This class wraps the GameController-related knowledge of Dashboard to avoid a circular import.

	You probably shouldn't use this class directly, but rather should use DashboardDelegateThread to
	run it in a background thread.
	"""
	game: GameController
	
	def __init__(self, game: GameController) -> None:
		self.game = game
	
	def make_statusline(self) -> str:
		"""
		Generate a statusline for the bottom right of the Dashboard window.
		"""
		self.game.arduino.update()
		return ' / '.join(' '.join(str(a) for a in x) for x in [
			("State:", self.game.state.name),
			("Gantry:", self.game.arduino.gantry_pos),
			("Magnet:", 'ON' if self.game.arduino.electromagnet_enabled else 'OFF'),
		])

	def execute_command(self, command: str):
		"""
		Execute a command given through the dashboard. This method receives the raw text of the command.
		"""
		cmd, *args = command.strip().lower().split(' ')

		if cmd == 'move':  # Move the gantry to a square
			square = chess.parse_square(args[0])
			print('Moving to square:', chess.square_name(square))
			self.game.move_to_square(square, block=False)
		elif cmd == 'magnet':  # Enable/disable the electromagnet
			enabled = args[0] == 'on'
			print('Turning magnet',  'ON' if enabled else 'OFF')
			self.game.arduino.set_electromagnet(args[0] == 'on', block=False)
		elif cmd == 'bled':  # Enable/disable button LEDs (bLEDs)
			enabled = args[1] == 'on'
			button = Button[args[0].upper()]
			print('Turning button light', button.name, 'ON' if enabled else 'OFF')
			self.game.arduino.set_button_light(button, enabled)
		elif cmd == 'leds':  # Set the current mode (pallete) of the LEDs around the board
			pallete = LEDPallete[args[0].upper()]
			print('Setting LEDs to Pallete:', pallete.name)
			self.game.arduino.set_led_pallete(pallete)
		elif cmd == 'autoplay':  # (De-)activate autoplay mode
			self.game.set_autoplay(args[0] == 'on')
		elif cmd == 'camshow':  # Show what the camera currently sees, with annotations from the CV pipeline
			print("Fetching image...")
			try:
				img = self.game.get_image(retry=0)
			except Exception as err:
				print("Failed to load image:", err)
				return
			print("Recognizing board...")
			try:
				positions = self.game.detector.detect_piece_positions(img, show=True)
				board = self.game.detector.generate_board(positions)
			except Exception as err:
				show_image(img)  # If we couldn't show the annotated version, show the raw version
				print("Failed to detect piece positions:", err)
				return
			# See comment in game_controller.py for why we show the question upside-down
			# TL;DR: that's the perspective Ari had when debugging
			print("Board (computer perspective):")
			print(board.transform(chess.flip_horizontal).transform(chess.flip_vertical))
		elif cmd == 'exit':
			exit(0)
		else:
			print(f"Unknown Command: '{command}'")


class DashboardDelegateThread(Thread):
	"""
	This class is responsible for starting and running the DashboardDelegate and GameController in a
	background thread to avoid blocking the UI.
	"""

	# This is an extremely primitive cross-thread communication system, but it's good enough for now
	# and the Dashboard is such a small part of the overal product that it wasn't worth investing in.
	status_line: str = 'Loading...'
	status_line_stale: bool = True
	commands: deque  # (de)queue of commands to execute
	# We aquire this lock when the thread starts and release it when the game controller is ready.
	wait_for_ready: Lock

	def __init__(self):
		super().__init__()
		self.commands = deque()
		self.wait_for_ready = Lock()

	def get_status_line(self):
		self.status_line_stale = True
		return self.status_line

	def run(self):
		with self.wait_for_ready:
			delegate = DashboardDelegate(GameController())
			delegate.game.arduino.update()  # Initialize data

		while True:
			# HACK: only generate status line updates when needed
			if self.status_line_stale:
				self.status_line = delegate.make_statusline()
			# arduino.update() listens for and dispatches button presses, therefore triggering all
			# real activity
			delegate.game.arduino.update()
			while len(self.commands) > 0:
				delegate.execute_command(self.commands.popleft())