try:
	import lib.apriltag.python.apriltag as apriltag
	is_linux = False
except ModuleNotFoundError:
	import dt_apriltags as apriltag
	is_linux = True

def detect_apriltag(family: str, image) -> apriltag.Detection:
	if is_linux:
		# TODO: use family
		return apriltag.Detector().detect(image)
	else:
		return apriltag.Detector(options=apriltag.DetectorOptions(families=family)).detect(image)