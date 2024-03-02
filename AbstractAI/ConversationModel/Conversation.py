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
	
	@property
	def all_message_sequences(self) -> List[MessageSequence]:
		if not hasattr(self, "_all_message_sequences"):
			if self.message_sequence is not None:
				self._all_message_sequences = [self.message_sequence]
			else:
				self._all_message_sequences = []
		return self._all_message_sequences
	
	def __post_init__(self):
		if self.message_sequence is not None:
			self.message_sequence.conversation = self
		def conversation_changed():
			self.last_modified = get_local_time()
		self.conversation_changed.connect(conversation_changed)
		
	def new_message_sequence(self):
		self.message_sequence = self.message_sequence.copy()
		self.message_sequence.conversation = self
		self.all_message_sequences.append(self.message_sequence)
		
	def add_message(self, message:Message):
		self.new_message_sequence()
		self.message_sequence.add_message(message)
	
	def remove_message(self, message:Message):
		self.new_message_sequence()
		self.message_sequence.remove_message(message)
	
	def remove_messages(self, messages:List[Message]):
		self.new_message_sequence()
		self.message_sequence.remove_messages(messages)
		
	def replace_message(self, old_message:Message, new_message:Message, keeping_latter:bool=False):
		self.new_message_sequence()
		self.message_sequence.replace_message(old_message, new_message, keeping_latter)
	
	def alternates(self, message:Message) -> List[MessageSequence]:
		'''
		Returns a list of MessageSequences that have the same messages as
		conversation.message_sequence up to message.
		
		If message is None, returns a list of MessageSequences that have
		the same messages as conversation.message_sequence up to the last
		message.
		'''
		messages_to_match = [msg.auto_id for msg in self.message_sequence.messages]
		if message is not None and message in messages_to_match:
			messages_to_match = messages_to_match[:messages_to_match.index(message.auto_id)+1]
		
		alternates = [
			ms for ms in self.all_message_sequences
			if [msg.auto_id for msg in
				ms.messages[:len(messages_to_match)]
				] == messages_to_match
		]
		return alternates