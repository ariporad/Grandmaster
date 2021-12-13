"""
A cross-platform wrapper for Apriltag libraries.

dt_apriltags only works on Linux while apriltag only works on macOS (arm64). They have very similar
APIs, so this module wraps them for seamless use.
"""
from typing import *
from collections import defaultdict

try:
	import lib.apriltag.python.apriltag as apriltag
	is_linux = False
except ModuleNotFoundError:
	import dt_apriltags as apriltag
	is_linux = True

def scan_for_apriltags(family: str, image) -> apriltag.Detection:
	if is_linux:
		# TODO: use family
		return apriltag.Detector().detect(image)
	else:
		return apriltag.Detector(options=apriltag.DetectorOptions(families=family)).detect(image)

def detect_apriltags(family: str, image) -> Dict[int, Optional[apriltag.Detection]]:
	tags: Dict[int, Optional[apriltag.Detection]] = defaultdict(lambda: None)
	
	for tag in scan_for_apriltags(family, image):
		tags[tag.tag_id] = tag
	
	return tags