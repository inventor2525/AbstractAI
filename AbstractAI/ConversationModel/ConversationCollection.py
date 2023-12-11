from AbstractAI.ConversationModel import *
from abc import ABC, abstractmethod

class ConversationCollection():
	@abstractmethod
	def add_conversation(self, conversation:Conversation) -> None:
		pass
	
	@abstractmethod
	def add_message(self, message:Message) -> None:
		pass
	
	@abstractmethod
	def add_message_sequence(self, message_sequence:MessageSequence) -> None:
		pass
	
	@abstractmethod
	def get_conversation(self, hash:str) -> Conversation:
		pass
	
	@abstractmethod
	def get_message(self, hash:str) -> Message:
		pass
	
	@abstractmethod
	def get_message_sequence(self, hash:str) -> MessageSequence:
		pass