from ClassyFlaskDB.Flaskify import Flaskify
from AbstractAI.ConversationModel import *

Flaskify.make_client(base_url="http://MyAIServer:8000")
from AbstractAI.Remote.System import System