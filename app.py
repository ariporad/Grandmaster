from flask import Flask
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'shhh!'
socketio = SocketIO(app)

def send_board():
	emit('board', 'the board is TBD')

@app.route('/')
def root():
	return "Hello, World!"

@socketio.on('connect')
def on_connect():
	send_board()

@socketio.event
def move(start_pos, end_pos):
	print("Got Move:", start_pos, '->', end_pos)
	send_board()

if __name__ == '__main__':
	socketio.run(app)