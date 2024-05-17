from AbstractAI.Model.Decorator import *
from AbstractAI.Helpers.Signal import Signal
from .MessageSequence import MessageSequence
from .Message import Message

from datetime import datetime
from typing import Callable, List, Union

@DATA(excluded_fields=["all_message_sequences"])
@dataclass
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
		self._ensure_all_message_sequences()
		return self._all_message_sequences
	
	def __post_init__(self):
		if self.message_sequence is not None:
			self.message_sequence.conversation = self
		def conversation_changed():
			self.last_modified = get_local_time()
		self.conversation_changed.connect(conversation_changed)
		
	def new_message_sequence(self):
		self._ensure_all_message_sequences()
		self.message_sequence = self.message_sequence.copy()
		self.message_sequence.conversation = self
		self._all_message_sequences.append(self.message_sequence)
		
	def add_message(self, message:Message):
		self.new_message_sequence()
		self.message_sequence.add_message(message)
	
	def insert_message(self, message:Message, index:int):
		self.new_message_sequence()
		self.message_sequence.insert_message(message, index)
		
	def remove_message(self, message:Message, silent=False):
		self.new_message_sequence()
		self.message_sequence.remove_message(message, silent)
	
	def remove_messages(self, messages:List[Message]):
		self.new_message_sequence()
		self.message_sequence.remove_messages(messages)
		
	def replace_message(self, old_message:Message, new_message:Message, keeping_latter:bool=False):
		self.new_message_sequence()
		self.message_sequence.replace_message(old_message, new_message, keeping_latter)
	
	def alternates(self, message:Union[Message,int]) -> List[MessageSequence]:
		'''
		Returns a list of MessageSequences that have the same messages as
		conversation.message_sequence up to message (inclusively).
		
		If message is None or less than 0, returns all_message_sequences.
		
		If message is an integer, it is used as an index into message_sequence.
		If message is greater than the length of message_sequence, all message
		sequences that start with the contents of message_sequence are returned.
		'''
		if message is None:
			return self.all_message_sequences
		
		if isinstance(message, int):
			if message < 0:
				return self.all_message_sequences
			elif message < len(self.message_sequence.messages):
				message = self.message_sequence.messages[message]
			else:
				message = self.message_sequence.messages[-1]
		
		messages_to_match = [msg.auto_id for msg in self.message_sequence.messages]
		if message.auto_id in messages_to_match:
			messages_to_match = messages_to_match[:messages_to_match.index(message.auto_id)+1]
		
		alternates = [
			ms for ms in self.all_message_sequences
			if [msg.auto_id for msg in
				ms.messages[:len(messages_to_match)]
				] == messages_to_match
		]
		
		return alternates
	
	def _ensure_all_message_sequences(self):
		if not hasattr(self, "_all_message_sequences"):
			if self.message_sequence is not None:
				self._all_message_sequences = [self.message_sequence]
			else:
				self._all_message_sequences = []
	
	def __iter__(self):
		return iter(self.message_sequence)
	
	def __getitem__(self, index):
		return self.message_sequence[index]
	
	def __len__(self):
		return len(self.message_sequence)
	
	def __contains__(self, message):
		return message in self.message_sequence