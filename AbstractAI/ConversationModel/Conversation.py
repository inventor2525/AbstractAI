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
	
	conversation_changed:Signal[[],None] = Signal.field()
	message_added:Signal[[Message],None] = Signal.field()
	message_removed:Signal[[Message],None] = Signal.field()
	
	def __post_init__(self):
		if self.message_sequence is not None:
			self.message_sequence.conversation = self
		self.conversation_changed.connect(self.update_message_graph)
		
	def new_message_sequence(self):
		self.message_sequence = self.message_sequence.copy()
		self.message_sequence.conversation = self
		
	def add_message(self, message:Message):
		self.new_message_sequence()
		self.message_sequence.add_message(message)
		self.last_modified = get_local_time()
	
	def remove_message(self, message:Message):
		self.new_message_sequence()
		self.message_sequence.remove_message(message)
		self.last_modified = get_local_time()
		
	def replace_message(self, old_message:Message, new_message:Message, keeping_latter:bool=False):
		self.new_message_sequence()
		self.message_sequence.replace_message(old_message, new_message, keeping_latter)
		self.last_modified = get_local_time()
		
	def update_message_graph(self):
		pass