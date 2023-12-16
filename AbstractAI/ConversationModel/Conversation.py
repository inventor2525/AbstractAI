from AbstractAI.ConversationModel.ModelBase import *
from .MessageSequence import MessageSequence
from .Message import Message

from datetime import datetime
from typing import List

@DATA
class Conversation:
	name: str = "Conversation"
	description: str = ""
	
	creation_time: datetime = field(default_factory=get_local_time)
	
	message_sequence: MessageSequence = field(default_factory=MessageSequence)
	
	_all_messages: List[Message] = field(default_factory=list)
	_root_messages: List[Message] = field(default_factory=list)

	def __post_init__(self):
		self.message_sequence.conversation = self
		
	def new_message_sequence(self):
		self.message_sequence = self.message_sequence.copy()
		
	def add_message(self, message:Message):
		self.message_sequence.add_message(message)
		self._all_messages.append(message)
	
	def remove_message(self, message:Message):
		self.message_sequence.remove_message(message)
		
	def replace_message(self, old_message:Message, new_message:Message, keeping_latter:bool=False):
		self.message_sequence.replace_message(old_message, new_message, keeping_latter)
		self._all_messages.append(new_message)
		
	def update_message_graph(self):
		self._root_messages = []
		
		for message in self._all_messages:
			if message.prev_message is None:
				self._root_messages.append(message)
			
			message._children = []
			for possible_child in self._all_messages:
				if possible_child.prev_message is message:
					message._children.append(possible_child)
					
			message._children.sort(key=lambda m: m.creation_time)
		
		self._root_messages.sort(key=lambda m: m.creation_time)