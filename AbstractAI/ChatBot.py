from AbstractAI.Conversation import *
from AbstractAI.LLMs.LLM import LLM, LLM_RawResponse
from AbstractAI.DB.ConversationCollection import ConversationCollection

class ChatBot:
	def __init__(self, model:LLM, db:ConversationCollection, conversation:Conversation=None):
		self.model = model
		self.db = db
		
		if conversation is None:
			conversation = Conversation()
		self.conversation = conversation
		
		self.default_role = Role.User
		self.default_source = UserSource()
		
		self.last_response = None
		self.model.start()
		
	def prompt(self, prompt:str, role:Role=None, source:BaseMessageSource=None) -> str:
		if role is None:
			role = self.default_role
		if source is None:
			source = self.default_source
			
		msg = Message(prompt, role, source)
		self.conversation.add_message(msg)
		self.db.add_conversation(self.conversation)
		
		self.last_response = self.model.prompt(self.conversation)
		
		self.conversation.add_message(self.last_response.message)
		self.db.add_conversation(self.conversation)
		return self.last_response.message.content