from camera.camera import Camera
from chess_controller import ChessController
from arduino_controller import ArduinoController
from enum import IntEnum, auto

class State(IntEnum):
	READY = auto()
	HUMAN_TURN = auto()
	COMPUTER_TURN = auto()
	ENDED = auto()

class GameController:
	arduino: ArduinoController
	chess: ChessController
	camera: Camera

	def __init__(self, camera_calibration='calibration.json'):
		self.camera = Camera(camera_calibration=camera_calibration)
		self.chess = ChessController()
		self.arduino = ArduinoController()

	def main():
		pass