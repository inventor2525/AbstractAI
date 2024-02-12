from ClassyFlaskDB.Flaskify import *

if __name__ == '__main__':
	# Make a server:
	app = Flask(__name__)
	Flaskify.make_server(app)
	from AbstractAI.Remote.System import System
	from AbstractAI.LLMs.RemoteLLM import RemoteLLM_Backend
	
	# Debug what routes are available:
	Flaskify.debug_routes()
	
	# Start the server:
	System.start_server()
	app.run(host='0.0.0.0', port=8000)