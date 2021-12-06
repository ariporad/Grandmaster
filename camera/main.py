import cv2
import chess
from sys import argv
from chess_controller import ChessController
from random import choice
from serial import Serial
from time import sleep

if "--help" in argv:
	print(f"""
Instructions:

--nocv     - skip computer vision, always make move c6f2
--nocamera - don't use the camera, just load an image from realboard.jpg
--nomove   - only do CV, don't move the gantry
--help     - show this message and exit

	""".strip())
	exit(0)

if "--nocv" in argv:
	move = chess.Move.from_uci("c6f2")
else:
	chess_controller = ChessController()

	if '--nocamera' in argv:
		print("Skipping camera, loading realboard.jpg")
		img = cv2.imread('realboard.jpg')
	else:
		from camera import Camera
		camera = Camera()

		img = camera.capture_frame()
		cv2.imwrite("main.jpg", img)
		print("Used camera, wrote image to main.jpg")

	if img is None:
		print("FAILED TO LOAD IMAGE!")

	board = chess_controller.get_current_board(img)
	# pieces = detector.detect_piece_positions(img)
	# board = chess.Board(None)

	# for location, letter in pieces:
	# 	board.set_piece_at(chess.parse_square(location), chess.Piece.from_symbol(letter))

	print("SCANNED BOARD:")
	print(board)

	board.turn = chess.BLACK
	turns = list(board.legal_moves)
	print("Legal Computer Moves:", turns)

	move = chess_controller.pick_move(board)

if "--nomove":
	print("Not moving, but would:", move)
else:
	print("Moving:", move)

	gantry = Serial(port='/dev/ttyACM0', baudrate=115200, timeout=0.1)
	# board = Serial(port='/dev/whatever', baudrate=115200, timeout=0.1)

	print("Move to Square:", chess.square_name(move.from_square), "=", move.from_square)
	gantry.write(bytes(str(move.from_square), 'utf-8'))
	sleep(10)

	print("SKIPPING: Turn On Magnet")
	# board.write(bytes('1', 'utf-8'))
	# sleep(2)

	print("Move to Square:", chess.square_name(move.to_square), "=", move.to_square)

	gantry.write(bytes(str(move.to_square), 'utf-8'))
	gantry.flush()
	sleep(10)

	print("SKIPPING: Turn Off Magnet")

	# board.write(bytes('0', 'utf-8'))
	# sleep(2)

	print("Moving Away")

	gantry.write(bytes(str(move.to_square - 1), 'utf-8'))
	gantry.flush()
	print("Done")