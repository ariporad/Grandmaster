from typing import *
from helpers import print_to_dashboard as print

import cv2
import chess
import requests
import numpy as np
from time import sleep
from enum import Enum
from random import choice
from detector import Detector
from arduino_manager import ArduinoManager, Button, LEDPallete

class State(Enum):
	STARTING = 'STARTING'
	READY = 'READY'
	HUMAN_TURN = 'HUMAN_TURN'
	COMPUTER_TURN = 'COMPUTER_TURN'
	ERROR = 'ERROR'

class GameController:
	"""
	The GameController is the brain of the entire Grandmaster Chess Board. It's responsible for
	coordinating all subsystems and for all high-level logic.
	"""
	state: State = State.STARTING
	arduino: ArduinoManager
	autoplay: bool = False

	def __init__(self):
		self.detector = Detector()
		self.arduino = ArduinoManager(self.enter_ready_state, {
			(Button.PLAYER): self.play_computer_turn,
			# For ease of debugging, the computer button behaves the same as the player button
			(Button.COMPUTER): self.play_computer_turn,
			(Button.FUN): lambda: self.set_autoplay(True),
			(Button.START): self.start
		})
	
	def set_autoplay(self, autoplay: bool):
		"""
		Enter or exit autoplay mode.
		"""
		print("Setting autoplay:", autoplay)
		was_autoplay = self.autoplay
		self.autoplay = autoplay
		if autoplay:
			self.state = State.HUMAN_TURN
			self.play_computer_turn()
		else:
			if was_autoplay:
				self.enter_ready_state()

	def enter_ready_state(self):
		"""
		Put the board into a ready-to-play state.
		"""
		self.state = State.READY
		self.autoplay = False
		self.arduino.set_button_light(Button.START, True, others=False)
		self.arduino.set_button_light(Button.FUN, True)
		self.arduino.set_led_pallete(LEDPallete.READY)
		print("Ready!")

	def start(self):
		"""
		Start a 1-player game. Invoked when the physical "Start" button is pressed.
		"""
		print("Starting a game...")
		self.set_autoplay(False)
		self.start_human_turn()

	def start_human_turn(self):
		"""
		Start the human's turn, which mostly consists of changing lights then waiting for the button
		to be pressed.

		In autoplay mode, this invokes play_computer_turn to actually play the turn.
		"""
		self.state = State.HUMAN_TURN
		if not self.autoplay:
			self.arduino.set_button_light(Button.PLAYER, True, others=False)
			self.arduino.set_led_pallete(LEDPallete.HUMAN_TURN)
		else:
			self.play_computer_turn(True)

	def play_computer_turn(self, is_autoplaying_human=False):
		"""
		Play the computer's turn. In autoplay mode, this is also used to play for the would-be human
		(with is_autoplaying_human=True).
		"""
		# Either the human's turn just ended (so now it's the computer's turn) or the human's turn
		# just started and we're in autoplay mode.
		if self.state != State.HUMAN_TURN: return
		
		print("My turn!" if not is_autoplaying_human else "My turn (on the human's behalf)!")
		if not is_autoplaying_human:
			self.state = State.COMPUTER_TURN
			self.arduino.set_button_light(Button.COMPUTER, True, others=False)
			self.arduino.set_led_pallete(LEDPallete.COMPUTER_THINK)
		else:
			self.arduino.set_button_light(Button.PLAYER, True, others=False)
			self.arduino.set_led_pallete(LEDPallete.AUTOPLAY_HUMAN_THINK)

		try:
			print("Fetching image...")
			img = self.get_image()
			print("Got image!")

			print("Analyzing Image...")
			# On the Grandmaster Chess Board, the human is always white (so they go first) and the computer is black
			board = self.detector.detect_board(img, chess.BLACK if not is_autoplaying_human else chess.WHITE)
			print("Got Board (from computer perspective):")
			print(board.transform(chess.flip_horizontal).transform(chess.flip_vertical))

			move: chess.Move = self.pick_move(board)

			print("Making Move:", board.piece_at(move.from_square), '@', move)
			self.arduino.set_led_pallete(LEDPallete.COMPUTER_MOVE if not is_autoplaying_human else LEDPallete.HUMAN_TURN)
			self.arduino.set_electromagnet(False)
			self.move_to_square(move.from_square)
			self.arduino.set_electromagnet(True)
			self.move_to_square(move.to_square)
			self.arduino.set_electromagnet(False)
			print("DONE with my turn!")
			if not is_autoplaying_human:
				self.start_human_turn()
			else:
				self.play_computer_turn(False)
		except Exception as err:
			print("Failed to execute move! Retrying in 3 seconds...!")
			print(err)
			# If we just don't acknowledge the failure it's like it never happened! #HashtagLifeHax
			# self.arduino.set_led_pallete(LEDPallete.FAIL)
			sleep(3)
			self.state = State.HUMAN_TURN # So we pass the guard condition at the beginning
			self.play_computer_turn(is_autoplaying_human) # Try again
	
	def pick_move(self, board: chess.Board):
		"""
		Select the best move to make from a set of options.

		Currently, Grandmaster employes a novel and unconventional chess algorithm: it picks moves
		at random, excluding moves involving a knight or a capture. (Both of which are more complex
		to physically execute.)
		
		This is an area with significant possible future improvement.
		"""
		return choice([
			move for move in board.legal_moves 
			if board.piece_at(move.from_square).piece_type != chess.KNIGHT \
				and board.piece_at(move.to_square) is None])

	def move_to_square(self, square: chess.Square, block=True):
		"""
		Move the gantry to the provided chess square.

		Light wrapper around ArduinoManager.move_gantry.
		"""
		x = chess.square_file(square)
		y = chess.square_rank(square)
		self.arduino.move_gantry(x, y, block)
	
	def get_image(self, retry=5):
		"""
		Fetch an image from the Grandmaster Vision Service (Raspberry Pi). Because the Vision
		Service is often flakey, this method automatically retries if nessecary.
		"""
		try:
			r = requests.get('http://grandmaster.local:5555/camera.png', stream=True).raw
			return cv2.imdecode(np.asarray(bytearray(r.read()), dtype='uint8'), cv2.IMREAD_COLOR)
		except Exception as err:
			if retry > 0:
				print(f"Failed to fetch image, retrying {retry} more times in 3 seconds!", err)
				sleep(3)
				return self.get_image(retry - 1)
			else:
				raise
