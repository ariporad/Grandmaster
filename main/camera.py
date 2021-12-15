import cv2
from helpers import print_to_dashboard as print
from os.path import dirname, join
from camera_calibration import CameraCalibration

class CameraError(Exception):
    pass

class Camera:
    """
    Light wrapper around OpenCV's camera APIs to make them slightly nicer to use, and to integrate
    calibration and distortion correction.
    """
    camera: cv2.VideoCapture
    calibration: CameraCalibration

    def __init__(self, camera_idx=0, calibration_file=join(dirname(__file__), 'calibration.json')):
        self.calibration = CameraCalibration.read(calibration_file)
        self.camera = cv2.VideoCapture(camera_idx)
        self.camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)

    @property
    def width(self):
        return self.calibration.width

    @property
    def height(self):
        return self.calibration.height

    def capture_frame(self):
        """
        Capture a frame from the camera. Image is guaranteed to be captured while this method is
        executing (ie. not buffered).
        """
        # There's an annoying frame buffer we want to drain
        for _ in range(1):
            self.camera.read()

        success, frame = self.camera.read()

        if not success:
            raise CameraError("Failed to read camera frame!")

        undistorted = cv2.undistort(
            frame, self.calibration.camera_matrix, self.calibration.distortion)

        return undistorted