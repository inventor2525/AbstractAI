from AbstractAI.ChatBot import *
from AbstractAI.Model.Converse import *
from AbstractAI.LLMs.ModelLoader import ModelLoader, LLM

from datetime import datetime

from ClassyFlaskDB.DATA import DATAEngine
data_engine = DATAEngine(DATA, engine_str="sqlite:///chat.db")

model_loader = ModelLoader()
model_name = None
model = None
while model is None:
	try:
		print("Select a model by name\nAvailable models:", model_loader.model_names)
		model_name = input(">>")
		model = model_loader[model_name]
	except KeyError as e:
		print(f"Failed to load model '{model_name}' with error: {e}")
		model = None
model.start()

conversations = ConversationCollection.all_from_engine(data_engine)
conv = None
while conv is None:
	try:
		print("Select a conversation by id from the list below, or type `new` for a new conversation\nAvailable conversations:")
		conversations_by_id = {}
		for conv in conversations:
			conversations_by_id[conv.auto_id] = conv
			print(f"{conv.name}\nID:{conv.auto_id}\nCreated at:{conv.date_created}\n{conv.description}\n")
		conv_id = input(">> ")
		if conv_id.lower() == "new":
			conv_name = input("Enter a name for the new conversation: ")
			if conv_name == "":
				conv_name = "New Chat"
			conv = Conversation(conv_name, f"chat created by chat.py at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
			conv.add_message(message=Message.HardCoded("You are a helpful assistant.", system_message=True))
			conversations.append(conv)
		else:
			conv = conversations_by_id[conv_id]
		if conv is None:
			raise Exception("Invalid option selected")
	except Exception as e:
		print(f"Failed to load conversation with error: {e}")
		conv = None

bot = ChatBot(model, conversations, conv)
while True:
	print(bot.prompt(input("> ")))