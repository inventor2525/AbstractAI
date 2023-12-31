from typing import List
from .Message import Message
from AbstractAI.Hashable import Hashable, hash_property

class MessageSequence(Hashable):
	'''A list of messages that can be passed to a Large Language Model'''
	def __init__(self, conversation:"Conversation" = None):
		super().__init__()
		self.messages:List[Message] = []
		
		# A weak reference to what conversation this is apart of.
		self.conversation = conversation
	
	@property
	def hashes(self):
		"""
		Get the hashes of all messages in the conversation.
		"""
		return [message.hash for message in self.messages]
		
	def recompute_hash(self):
		self._hash = self._compute_hash(tuple(self.hashes))
		
	def add_message(self, message: Message):
		message.conversation = self.conversation
		self.spoil_hash()
		if len(self.messages)>0:
			message.prev_message = self.messages[-1]
		self.messages.append(message)
	
	def remove_message(self, message: Message):
		self.spoil_hash()
		self.messages.remove(message)
		
	def replace_message(self, old_message:Message, new_message:Message, keeping_latter:bool=False):
		if keeping_latter:
			try:
				self.messages[self.messages.index(old_message)] = new_message
			except ValueError:
				pass
		else:
			found = False
			new_messages = []
			for m in self.messages:
				if m is old_message:
					found = True
					break
				else:
					new_messages.append(m)
					
			if found:
				self.messages = new_messages
				self.add_message(new_message)