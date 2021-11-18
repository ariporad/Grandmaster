import cv2
import chess
from sys import argv
from detector import Detector
from random import choice
from serial import Serial
from time import sleep


detector = Detector()

if '--camera' in argv:
	camera = cv2.VideoCapture(0)

	# There's an annoying frame buffer we want to drain
	for _ in range(15):
		camera.read()

	success, img = camera.read()

	if not success:
		print("FAILED TO READ CAMERA!")
else:
	img = cv2.imread('realboard.jpg')

if img is None:
	print("FAILED TO LOAD IMAGE!")

pieces = detector.detect_piece_positions(img)
board = chess.Board(None)

for location, letter in pieces:
	board.set_piece_at(chess.parse_square(location), chess.Piece.from_symbol(letter))

print("SCANNED BOARD:")
print(board)

board.turn = chess.BLACK
turns = list(board.legal_moves)
print("Legal Computer Moves:", turns)

move = choice(turns)

print("Moving:", move)

gantry = Serial(port='/dev/whatever', baudrate=115200, timeout=0.1)
board = Serial(port='/dev/whatever', baudrate=115200, timeout=0.1)

gantry.write(bytes(str(move.from_square), 'utf-8'))
sleep(10)

board.write(bytes('1', 'utf-8'))
sleep(2)

gantry.write(bytes(str(move.to_square), 'utf-8'))
sleep(10)

board.write(bytes('0', 'utf-8'))
sleep(2)

gantry.write(bytes(str(move.to_square - 1), 'utf-8'))
sleep(10)