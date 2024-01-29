from AbstractAI.ConversationModel.ModelBase import *
from AbstractAI.Helpers.Signal import Signal
from .MessageSequence import MessageSequence
from .Message import Message

from datetime import datetime
from typing import Callable, List

@ConversationDATA
class Conversation:
	name: str = "Conversation"
	description: str = ""
	
	creation_time: datetime = field(default_factory=get_local_time)
	last_modified: datetime = field(default_factory=get_local_time)
	
	message_sequence: MessageSequence = field(default_factory=MessageSequence)
	
	message_added:Signal[[Message],None] = Signal.field()
	
	#_all_messages: List[Message] = field(default_factory=list)
	#_root_messages: List[Message] = field(default_factory=list)

	def __post_init__(self):
		self.message_sequence.conversation = self
		
	def new_message_sequence(self):
		self.message_sequence = self.message_sequence.copy()
		
	def add_message(self, message:Message):
		self.message_sequence.add_message(message)
		#self._all_messages.append(message)
		self.message_added(message)
		self.last_modified = get_local_time()
	
	def remove_message(self, message:Message):
		self.message_sequence.remove_message(message)
		self.last_modified = get_local_time()
		
	def replace_message(self, old_message:Message, new_message:Message, keeping_latter:bool=False):
		self.message_sequence.replace_message(old_message, new_message, keeping_latter)
		#self._all_messages.append(new_message)
		self.last_modified = get_local_time()
		
	def update_message_graph(self):
		self._root_messages = []
		
		# for message in self._all_messages:
		# 	if message.prev_message is None:
		# 		self._root_messages.append(message)
			
		# 	message._children = []
		# 	for possible_child in self._all_messages:
		# 		if possible_child.prev_message is message:
		# 			message._children.append(possible_child)
					
		# 	message._children.sort(key=lambda m: m.creation_time)
		
		self._root_messages.sort(key=lambda m: m.creation_time)