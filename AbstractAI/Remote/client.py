from ClassyFlaskDB.Flaskify import Flaskify
from AbstractAI.ConversationModel import *

if __name__ == '__main__':	
	# Create a client:
	Flaskify.make_client(base_url="http://MyAIServer:8000")
	from AbstractAI.Remote.System import System
	
	# Load a llm on the server:
	System.load_LLM("stabilityai/StableBeluga-7B")
	
	# Prompt it:
	c = Conversation("Conversation", "First conversation")
	c.add_message(Message("Hello", UserSource("Charlie")))

	m = System.prompt_chat("stabilityai/StableBeluga-7B", c)
	print(m.content)