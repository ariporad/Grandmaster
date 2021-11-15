import cv2

cam = cv2.VideoCapture(0)

# For some reason the first frame is always all black, so throw it away
cam.read()

success, frame = cam.read()

if success:
    cv2.imshow("frame", frame)

    cv2.waitKey(0)
    cv2.destroyAllWindows()
else:
    print("FAILED to read camera!")
