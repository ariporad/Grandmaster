from dataclasses import dataclass
import json
import numpy as np
import cv2


@dataclass
class CameraCalibration:
    """
    A serializable data class to contain information about camera calibration.
    """
    camera_matrix: np.array
    distortion: np.array
    width: int
    height: int

    JSON_TYPE = 'edu.olin.pie.grandmaster.camera-calibration'

    def write(self, file):
        with open(file, 'w') as f:
            json.dump({
                'type': self.JSON_TYPE,
                'camera_matrix': self.camera_matrix.tolist(),
                'distortion': self.distortion.tolist(),
                'width': self.width,
                'height': self.height
            }, f)
    
    @classmethod
    def read(cls, file):
        with open(file, 'r') as f:
            data = json.load(f)
            assert data['type'] == cls.JSON_TYPE
            return cls(np.array(data['camera_matrix']), np.array(data['distortion']), data['width'], data['height'])


# From: https://www.geeksforgeeks.org/camera-calibration-with-python-opencv/

# TODO: need to calibrate on the same size image as the real thing, which means bigger chessboard


def calibrate(images, draw=False):
    """
    Calibrate a camera from some test images.
    """
    # Define the dimensions of checkerboard
    CHESSBOARD_SIZE_SQUARES = (6, 9)

    # stop the iteration when specified
    # accuracy, epsilon, is reached or
    # specified number of iterations are completed.
    criteria = (cv2.TERM_CRITERIA_EPS +
                cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)

    # Vectors for storing data for successfully processed images
    known_points_3D = []
    found_points_2D = []

    # Track success rate
    num_success = 0
    num_fail = 0

    # 3D points representing the known true positions of each square. We cheat by using units of
    # "one square width", so we can say that each square corner differs by 1 square and is in the
    # XY plane (Z = 0).
    KNOWN_BOARD_POSITIONS = np.zeros(
        (1, CHESSBOARD_SIZE_SQUARES[0] * CHESSBOARD_SIZE_SQUARES[1], 3),
        np.float32)
    KNOWN_BOARD_POSITIONS[0, :, :2] = \
        np.mgrid[0:CHESSBOARD_SIZE_SQUARES[0],
                 0:CHESSBOARD_SIZE_SQUARES[1]].T.reshape(-1, 2)

    for image in images:
        # Find the chess board corners
        success, corners1 = cv2.findChessboardCorners(
            image,
            CHESSBOARD_SIZE_SQUARES,
            # cv2.CALIB_CB_ADAPTIVE_THRESH + cv2.CALIB_CB_FAST_CHECK + cv2.CALIB_CB_NORMALIZE_IMAGE
        )

        if not success:
            print("Failed to find corners in image! Continuing...")
            num_fail += 1
            continue

        print("SUCCESS!")
        num_success += 1

        # Refine the positions of each corner
        corners2 = cv2.cornerSubPix(
            image, corners1, (11, 11), (-1, -1), criteria)

        # Store the corners we found
        found_points_2D.append(corners2)

        # Add the known truth to the list of 3D points once for each successful image
        known_points_3D.append(KNOWN_BOARD_POSITIONS)

        # Draw and display the corners
        if draw:
            image = cv2.drawChessboardCorners(image,
                                              CHESSBOARD_SIZE_SQUARES,
                                              corners2, success)
            cv2.imshow('Corners', image)
            cv2.waitKey(0)

    if len(found_points_2D) == 0:
        raise Exception("Couldn't detect any chessboards!")
    else:
        print(f"Processed {num_fail + num_success} images, {num_success} succeeded and {num_fail} failed.")
    
    img_shape = images[0].shape

    success, camera_matrix, distortion, rotation, translation = cv2.calibrateCamera(
        known_points_3D, found_points_2D, img_shape[::-1], None, None)

    if not success:
        raise Exception("Failed to calibrate camera!")

    return CameraCalibration(camera_matrix, distortion, height=img_shape[0], width=img_shape[1]) #, rotation, translation)


if __name__ == '__main__':
    """
    Simple CLI to generate a camera calibration from the images in calibration_test_images/*.jpg
    """
    import os
    from sys import argv
    draw = '--draw' in argv

    img_dir = 'calibration_test_images/'
    images = []

    print(f"Reading images from {img_dir}*.jpg")
    for file in os.listdir(img_dir):
        if file.endswith(".jpg"):
            path = os.path.join(img_dir, file)
            image = cv2.imread(path)
            image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            print("Read Image:", path)
            images.append(image)

    try:
        print("Calibrating...")
        calibration = calibrate(images, draw=draw)

        print("Successfully Calibrated Camera!")
        print("\nCamera Matrix:")
        print(calibration.camera_matrix)
        print("\nDistortion:")
        print(calibration.distortion)

        print("Writing to file (calibration.json)...")
        calibration.write('calibration.json')

        print("Undistorting test image...")

        undistorted = cv2.undistort(
            images[0], calibration.camera_matrix, calibration.distortion)

        print("Wrote to calibration_undistorted.jpg")
        cv2.imwrite('calibration_undistorted.jpg', undistorted)

        if draw:
            cv2.imshow("undistorted", undistorted)
            cv2.waitKey(0)
    finally:
        if draw:
            cv2.destroyAllWindows()
