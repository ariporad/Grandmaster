import cv2
from helpers import closest
from lib.apriltag.python.apriltag import Detector, DetectorOptions

APRILTAG_FAMILIES = ['tag36h11']
TEST_IMAGE = 'chessboard.png'

#
# Read Image & Run Detector
#

img = cv2.imread(TEST_IMAGE)
gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)

detector = Detector(DetectorOptions(families=APRILTAG_FAMILIES),
                    searchpath='lib/apriltag/build/lib')
detections, dimg = detector.detect(gray, return_image=True)

#
# Print Detections
#

# num_detections = len(detections)
# print('Detected {} tags.\n'.format(num_detections))

# for i, detection in enumerate(detections):
#     print('Detection {} of {}:'.format(i+1, num_detections))
#     print()
#     print(detection.tostring(indent=2))
#     print()

#
# Detect Corners
#
# Corner tags are on ranks 0 and 9, columns Alpha and I
# That's 9 squares of distance, center-to-center
#

corners = [tuple(d.center) for d in detections if d.tag_id < 128]
corners_x = sorted(x for x, y in corners)
corners_y = sorted(y for x, y in corners)

board_left_x = corners_x[0]
board_right_x = corners_x[-1]
board_top_y = corners_y[0]
board_bottom_y = corners_y[-1]

print(
    f"Board Corners: X: (L: {board_left_x}, R: {board_right_x}), Y: (T: {board_top_y}, B: {board_bottom_y})")

board_width = board_right_x - board_left_x
board_height = board_bottom_y - board_top_y

print(f"Board: H: {board_height}, W: {board_width}")

square_width = board_width / 9
square_height = board_height / 9

print(f"Square: H: {square_height}, W: {square_width}")

#
# Calculate Rank/File Centerlines
#

# Ranks and Files are both in the form of [('A', <centerpoint>), ...]
ranks = [(rank, board_bottom_y - (square_height * rank))
         for rank in range(1, 9)]
files = [(file, board_left_x + (square_height * (i + 1)))
         for i, file in enumerate('ABCDEFGH')]

print("Ranks:", *(f"{rank}={int(pos)}" for rank, pos in ranks))
print("Files:", *(f"{file}={int(pos)}" for file, pos in files))


#
# Calculate Piece Positions
#

pieces = sorted([detection for detection in detections if detection.tag_id >=
                128], key=lambda tag: tag.tag_id)

print("")
print("Pieces:")

for tag in pieces:
    x, y = tag.center
    file = closest(files, x, key=lambda x: x[1])
    rank = closest(ranks, y, key=lambda x: x[1])
    print(f"{tag.tag_id}: {file[0]}{rank[0]} @ ({x:>4.0f}, {y:>4.0f})")
