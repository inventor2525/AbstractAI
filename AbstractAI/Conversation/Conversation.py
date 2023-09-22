from typing import List
from .Message import Message
from AbstractAI.Hashable import Hashable, hash_property
from .MessageSequence import MessageSequence
from datetime import datetime

class Conversation(Hashable):
	'''A list of messages that can be passed to a Large Language Model'''
	def __init__(self, name:str="", description:str="", creation_time:datetime=None):
		super().__init__()
		if creation_time is None:
			creation_time = datetime.now()
		self.creation_time = creation_time
		
		self.name = name
		self.description = description
		
		self.all_messages:List[Message] = []
		self.message_sequence = MessageSequence(self)
		self.hash_spoiled.add(self._hash_spoiled)
		
		self.root_messages:List[Message] = []
	
	@hash_property
	def creation_time(self, value: datetime):
		"""The description of the conversation."""
		pass
	
	# @hash_property
	# def name(self, value: str):
	# 	"""The name of the conversation."""
	# 	pass
	
	# @hash_property
	# def description(self, value: str):
	# 	"""The description of the conversation."""
	# 	pass
	
	def _hash_spoiled(self):
		if self.message_sequence is not None:
			self.message_sequence.spoil_hash()
	
	def add_message(self, message:Message):
		self.message_sequence.add_message(message)
		self.all_messages.append(message)
	
	def remove_message(self, message:Message):
		self.message_sequence.remove_message(message)
		
	def replace_message(self, old_message:Message, new_message:Message, keeping_latter:bool=False):
		self.message_sequence.replace_message(old_message, new_message, keeping_latter)
		self.all_messages.append(new_message)
		
	def update_message_graph(self):
		self.root_messages = []
		
		for message in self.all_messages:
			if message.prev_message is None:
				self.root_messages.append(message)
			
			message.children = []
			for possible_child in self.all_messages:
				if possible_child.prev_message is message:
					message.children.append(possible_child)
					
			message.children.sort(key=lambda m: m.creation_time)
		
		self.root_messages.sort(key=lambda m: m.creation_time)