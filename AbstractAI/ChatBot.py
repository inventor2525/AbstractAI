from AbstractAI.ConversationModel import *
from AbstractAI.LLMs.LLM import LLM, LLM_RawResponse
from AbstractAI.ConversationModel.ConversationCollection import ConversationCollection

class ChatBot:
	def __init__(self, model:LLM, conversations:ConversationCollection, conversation:Conversation=None, fallback_model:LLM=None):
		self.model = model
		self.fallback_model = fallback_model
		self.conversations = conversations
		
		if conversation is None:
			conversation = Conversation()
		self.conversation = conversation
		
		self.default_source = UserSource()
		
		self.last_response = None
		self.model.start()
		
	def prompt(self, prompt:str, source:MessageSource=None) -> str:
		if source is None:
			source = self.default_source
			
		msg = Message(prompt, source)
		self.conversation.add_message(msg)
		self.conversations.add_conversation(self.conversation)
		
		self.last_response = LLM_RawResponse("Output Error", None, 0)
		
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
				
		self.conversation.add_message(self.last_response.message)
		self.conversations.add_conversation(self.conversation)
		return self.last_response.message.content