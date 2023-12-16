from ClassyFlaskDB.Flaskify import Flaskify
from AbstractAI.ConversationModel import *

if __name__ == '__main__':	
	# Create a client:
	Flaskify.make_client(base_url="http://MyAIServer:8000")
	from AbstractAI.Remote.System import System
	
	# Load a llm on the server:
	System.load_LLM("stabilityai/StableBeluga-7B")
	
	# Prompt it:
	def terminal_help(prompt:str) -> str:
		c = Conversation("Conversation", "First conversation")
		c.add_message(Message(r"""You are part of an automated system designed to convert prompts from a user into bash commands that can be run. Format is especially important. You must reply in the format of a bash script with nothing before or after. Be sure not to use files that you don't know exist. For example:

User: git commit all my work with the message "I did some stuff"
Assistant:```bash
	git add .;
	git commit -m "I did some stuff";
```

User: install git and checkout AbstractAI from Inventor2525 on github
Assistant:```bash
	sudo apt install git;
	git clone git@github.com:inventor2525/AbstractAI.git
```""", UserSource("Charlie", system_message=True)))
		c.add_message(Message(prompt, UserSource("Charlie")))

		m = System.prompt_chat("stabilityai/StableBeluga-7B", c)
		return m.content
	
	print(terminal_help("Create a conda environment called 'my_greate_env' and install transformers in it."))