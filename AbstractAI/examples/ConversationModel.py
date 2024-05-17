from AbstractAI.ConversationModel import *
from ClassyFlaskDB.DATA import *

from AbstractAI.ConversationModel.MessageSources.CallerInfo import CallerInfo

engine = DATAEngine(DATA, engine_str="sqlite:///ConversationModel.db")

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
		CallerInfo.catch_here_and_caller()
		model_source = ModelSource("Example Model", "An example model.")
		m = Message("A Response", source=model_source)
		self.conversation.add_message(m)

class TryErOut:
	def __init__(self) -> None:
		self.bot = Chatbot()
		self.bot.talk("Hello, World!")
		self.bot.add_hardcoded()
		self.bot.generate()
	
	def print(self):
		for message in self.bot.conversation.message_sequence.messages:
			print(message.source.caller_source)
			
		print_DATA_json(self.bot.conversation.to_json())
		engine.merge(self.bot.conversation)

if __name__ == "__main__":
	TryErOut().print()