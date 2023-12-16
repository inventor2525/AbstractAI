from flask import Flask
from ClassyFlaskDB.Flaskify import Flaskify

app = Flask(__name__)
Flaskify.make_server(app)

from AbstractAI.Remote.System import System

Flaskify.debug_routes()

if __name__ == '__main__':
	System.start_server()
	app.run(host='0.0.0.0', port=8000)