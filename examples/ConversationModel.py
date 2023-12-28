from AbstractAI.ConversationModel import *
from ClassyFlaskDB.DATA import *

from AbstractAI.ConversationModel.MessageSources.CallerInfo import CallerInfo

engine = DATAEngine(ConversationDATA, engine_str="sqlite:///ConversationModel.db")

class Chatbot:
	def __init__(self):
		self.name = "thing"
		self.user = UserSource("Test User")
		self.conversation = Conversation("Example Conversation", "A conversation to show the ConversationModel.")
	
		self.conversation.add_message(Message.HardCoded("Hello, World!", system_message=True))
	
	def talk(self, content:str):
		m = Message(content, source=self.user)
		self.conversation.add_message(m)
		return m
	
	def add_hardcoded(self):
		m = Message.HardCoded("A Response", system_message=False)
		self.conversation.add_message(m)
		return m
	
	def generate(self):
		CallerInfo.catch_now()
		model_source = ModelSource("Example Model", "An example model.")
		m = Message("A Response", source=model_source)
		self.conversation.add_message(m)
		
bot = Chatbot()
bot.talk("Hello, World!")
bot.add_hardcoded()
bot.generate()

for message in bot.conversation.message_sequence.messages:
	print(message.source.caller_source)
	
print_DATA_json(bot.conversation.to_json())
engine.merge(bot.conversation)