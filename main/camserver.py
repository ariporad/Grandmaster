import cv2
from time import time
from random import randint
from flask import Flask, make_response
from cam import Camera

app = Flask(__name__)
cam = Camera()

start_time = time()
fav_number = randint(1, 1000)

@app.route('/camera.png')
def camera():
	img = cam.capture_frame()
	success, buffer = cv2.imencode('.png', img)

	if not success:
		return 500

	return buffer.tobytes(), { 'Content-Type': 'image/png' }


@app.route('/info.json')
def info():
	return { 'ok': True, 'name': 'grandmaster:camserver', 'uptime': time() - start_time, 'favorite_number': fav_number }
	

@app.route('/')
def home():
	return f"""
<!DOCTYPE html>
<html>
<head>
<title>Grandmaster Vision Service</title>
</head>
<body>
<h1>Grandmaster OK!</h1>
<h3>Camera:</h3>
<img src="/camera.jpg" />
<button onclick="window.document.location.reload()">Refresh</button>
</body>
</html>
"""

if __name__ == '__main__':
	app.run(host='0.0.0.0', port='5555')