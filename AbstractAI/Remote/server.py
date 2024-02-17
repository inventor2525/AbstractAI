from ClassyFlaskDB.Flaskify import *
from AbstractAI.Helpers.Stopwatch import Stopwatch
if __name__ == '__main__':
	Stopwatch.singleton = Stopwatch(True)
	# Make a server:
	app = Flask(__name__)
	Flaskify.make_server(app)
	from AbstractAI.Remote.System import System
	from AbstractAI.LLMs.RemoteLLM import RemoteLLM_Backend
	
	# Debug what routes are available:
	Flaskify.debug_routes()
	
	# Start the server:
	System.start_server()
	Flaskify.start()
	app.run(host='0.0.0.0', port=8000)