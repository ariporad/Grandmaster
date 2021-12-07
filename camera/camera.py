import cv2
from calibrate import CameraCalibration

class CameraError(Exception):
        pass

class Camera:
        camera: cv2.VideoCapture
        calibration: CameraCalibration

        def __init__(self, camera_idx=0, calibration_file='calibration.json'):
                self.calibration = CameraCalibration.read(calibration_file)
                self.camera = cv2.VideoCapture(camera_idx)
                self.camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
                self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)

        def capture_frame(self):
                # There's an annoying frame buffer we want to drain
                for _ in range(15):
                        self.camera.read()

                success, frame = self.camera.read()

                if not success:
                        raise CameraError("Failed to read camera frame!")

                undistorted = cv2.undistort(
                    frame, self.calibration.camera_matrix, self.calibration.distortion)

                return undistorted