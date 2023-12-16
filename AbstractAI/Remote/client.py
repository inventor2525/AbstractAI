from ClassyFlaskDB.Flaskify import Flaskify
from AbstractAI.ConversationModel import *

if __name__ == '__main__':
	Flaskify.make_client(base_url="http://MyAIServer:8000")
	from AbstractAI.Remote.System import System

	System.load_LLM("stabilityai/StableBeluga-7B")
	
	c = Conversation("Conversation", "First conversation")
	c.add_message(Message("Hello", UserSource("Charlie")))

	m = System.prompt_chat(c)
	print(m.content)