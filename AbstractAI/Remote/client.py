from ClassyFlaskDB.Flaskify import Flaskify
from AbstractAI.Model.Converse import *

Flaskify.make_client(base_url="http://MyAIServer:8000")
from AbstractAI.Remote.System import System
from AbstractAI.LLMs.RemoteLLM import RemoteLLM

Flaskify.start()