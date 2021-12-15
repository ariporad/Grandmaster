from typing import *
from helpers import print_to_dashboard as print

import cv2
import chess
import requests
import numpy as np
import serial
import serial.tools.list_ports
from time import sleep
from enum import IntEnum, auto
from camera import Camera
from random import choice
from detector import Detector
from arduino_manager import ArduinoManager, Button, LEDPallete

class State(IntEnum):
	HUMAN_TURN = 0
	COMPUTER_TURN = 1
	ENDED = 2
	FAIL = 3

class GameController:
	arduino: ArduinoManager
	camera: Camera
	state: State = State.HUMAN_TURN
	gantry: serial.Serial

	autoplay: bool = False

	def __init__(self):
		self.camera = Camera()
		self.detector = Detector()
		self.arduino = ArduinoManager()
		self.arduino.on_button_press(Button.PLAYER, self.play_computer_turn)
		self.arduino.on_button_press(Button.COMPUTER, self.play_computer_turn)
		self.arduino.on_button_press(Button.FUN, lambda: self.set_autoplay(True))
		self.arduino.on_button_press(Button.START, lambda: self.set_autoplay(False))

	def set_autoplay(self, autoplay: bool):
		print("Setting autoplay:", autoplay)
		self.autoplay = autoplay
		if autoplay:
			self.state = State.HUMAN_TURN
			self.play_computer_turn()

	def play_computer_turn(self, is_autoplaying_human=False):
		if self.state != State.HUMAN_TURN: return
		
		print("My turn!")
		if not is_autoplaying_human:
			self.state = State.COMPUTER_TURN
			self.arduino.set_button_light(Button.COMPUTER, True, others=False)
			self.arduino.set_led_pallete(LEDPallete.COMPUTER_THINK)
		else:
			self.arduino.set_led_pallete(LEDPallete.EXPO_HUMAN_THINK)

		try:
			print("Fetching image...")
			img = self.get_image()
			print("Got image!")

			board = self.detector.detect_board(img, show=False)
			print("Got Board:")
			print(board.transform(chess.flip_horizontal).transform(chess.flip_vertical))
			if is_autoplaying_human:
				board.turn = chess.WHITE
			move: chess.Move = self.pick_move(board)
			print("Making Move:", board.piece_at(move.from_square), '@', move)

			self.arduino.set_led_pallete(LEDPallete.COMPUTER_MOVE if not is_autoplaying_human else LEDPallete.HUMAN_TURN)
			self.arduino.set_electromagnet(False)
			self.move_to_square(move.from_square)
			self.arduino.set_electromagnet(True)
			self.move_to_square(move.to_square)
			self.arduino.set_electromagnet(False)

			print("DONE! It's the human's turn now!")
			self.start_human_turn()
		except Exception as err:
			print("Failed to execute computer turn! Retrying in 3 seconds...!")
			print(err)
			self.arduino.set_led_pallete(LEDPallete.FAIL)
			sleep(3)
			self.state = State.HUMAN_TURN
			self.play_computer_turn(is_autoplaying_human)
	
	def pick_move(self, board: chess.Board):
		return choice([
			move for move in board.legal_moves 
			if board.piece_at(move.from_square).piece_type != chess.KNIGHT \
				and board.piece_at(move.to_square) is None])

	def start_human_turn(self):
		self.state = State.HUMAN_TURN
		if not self.autoplay:
			self.arduino.set_button_light(Button.PLAYER, True, others=False)
			self.arduino.set_led_pallete(LEDPallete.HUMAN_TURN)
		else:
			self.play_computer_turn(True)

	def move_to_square(self, square: chess.Square, block=True):
		x = chess.square_file(square)
		y = chess.square_rank(square)
		self.arduino.move_gantry(x, y, block)
	
	def get_image(self, retry=5):
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
	
	def main(self):
		self.arduino.update()
		print("Grandmaster Ready")
		self.start_human_turn()
		while True:
			self.arduino.update()
