from AbstractAI.Model.Converse import *
from AbstractAI.LLMs.LLM import LLM, LLM_Response
from AbstractAI.Model.Converse.ConversationCollection import ConversationCollection

class ChatBot:
	def __init__(self, model:LLM, conversations:ConversationCollection, conversation:Conversation=None, fallback_model:LLM=None):
		self.model = model
		self.fallback_model = fallback_model
		self.conversations = conversations
		
		if conversation is None:
			conversation = Conversation()
			conversations.append(conversation)
		self.conversation = conversation
		
		self.default_source = UserSource()
		
		self.last_response = None
		
	def prompt(self, prompt:str, source:MessageSource=None) -> str:
		if source is None:
			source = self.default_source
			
		msg = Message(prompt, source)
		self.conversation.add_message(msg)
		
		self.last_response = None
		
		try:
			self.last_response = self.model.chat(self.conversation)
		except:
			if self.fallback_model is not None:
				try:
					self.last_response = self.fallback_model.chat(self.conversation)
				except:
					pass
			else:
				pass
		
		if self.last_response is None:
			return None
		
		self.conversation.add_message(self.last_response.message)
		return self.last_response.message.content