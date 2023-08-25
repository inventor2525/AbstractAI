from typing import List
from .Message import *
from AbstractAI.Hashable import Hashable

class Conversation(Hashable):
	'''A list of messages that can be passed to a Large Language Model'''
	def __init__(self, name:str="", description:str=""):
		super().__init__()
		self.name = name
		self.description = description
		self.messages:List[Message] = []
	
	@property
	def hashes(self):
		"""
		Get the hashes of all messages in the conversation.
		"""
		return [message.hash for message in self.messages]
		
	def recompute_hash(self):
		self._hash = self._compute_hash(tuple(self.hashes))
		
	def add_message(self, message: Message):
		self.messages.append(message)