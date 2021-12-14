from typing import *
from sys import exit
import chess
from prompt_toolkit.completion import Completer, NestedCompleter
from game_controller import GameController
from arduino_manager import Button
from helpers import print_to_dashboard as print, show_image

class DashboardDelegate:
	"""
	This class wraps the GameController-related knowledge of Dashboard to avoid a circular import.
	"""
	game: GameController
	
	def __init__(self, game: GameController) -> None:
		self.game = game
	
	def make_statusline(self) -> str:
		self.game.arduino.update()
		return ' / '.join(' '.join(str(a) for a in x) for x in [
			("State:", self.game.state.name),
			("Gantry:", self.game.arduino.gantry_pos),
			("Magnet:", 'ON' if self.game.arduino.electromagnet_enabled else 'OFF'),
		])

	def make_completer(self) -> Completer:
		return NestedCompleter(ignore_case=True, options={
			'move': chess.SQUARE_NAMES,
			'magnet': {'on', 'off'},
			'bled': {(b.name): {'on', 'off'} for b in Button},
			'camshow': None,
			'exit': None
		})

	def execute_command(self, command: str):
		cmd, *args = command.strip().lower().split(' ')

		if cmd == 'move':
			square = chess.parse_square(args[0])
			print('Moving to square:', chess.square_name(square))
			self.game.move_to_square(square, block=False)
		elif cmd == 'magnet':
			enabled = args[0] == 'on'
			print('Turning magnet',  'ON' if enabled else 'OFF')
			self.game.arduino.set_electromagnet(args[0] == 'on', block=False)
		elif cmd == 'bled':
			enabled = args[1] == 'on'
			button = Button[args[0].upper()]
			print('Turning button light', button.name, 'ON' if enabled else 'OFF')
			self.game.arduino.set_button_light(button, enabled)
		elif cmd == 'camshow':
			print("Fetching image...")
			try:
				img = self.game.get_image(retry=0)
			except Exception as err:
				print("Failed to load image:", err)
				return
			print("Recognizing board...")
			try:
				positions = self.game.detector.detect_piece_positions(img, on_annotate=show_image)
				board = self.game.detector.generate_board(positions)
			except Exception as err:
				show_image(img)
				print("Failed to detect piece positions:", err)
				return
			print("Board:")
			print(board)
		elif cmd == 'exit':
			exit(0)
		else:
			print(f"Unknown Command: '{command}'")


	def main(self):
		return self.game.main()