from ClassyFlaskDB.DefaultModel import *
from .Message import Message
from typing import List, Optional

@DATA(generated_id_type=ID_Type.HASHID, hashed_fields=["messages"])
@dataclass
class MessageSequence(Object):
	messages: List[Message] = field(default_factory=list)
	conversation: "Conversation" = field(default=None, compare=False)
	
	def add_message(self, message: Message):
		self._add_message(message)
		self.new_id()
		
		if self.conversation is not None:
			self.conversation.message_added(message)
			self.conversation.conversation_changed()
	
	def insert_message(self, message: Message, index:int):
		message.conversation = self.conversation
		
		if index > 0:
			message.prev_message = self.messages[index-1]
		self.messages.insert(index, message)
		self.new_id()
		
		if self.conversation is not None:
			self.conversation.message_added(message)
			self.conversation.conversation_changed()
	
	def remove_message(self, message: Message, silent:bool=False):
		self.messages.remove(message)
		self.new_id()
		
		if not silent and self.conversation is not None:
			self.conversation.message_removed(message)
			self.conversation.conversation_changed()
	
	def remove_messages(self, messages_to_remove: List[Message]):
		new_messages = []
		removed_messages = []
		for m in self.messages:
			if m in messages_to_remove:
				removed_messages.append(m)
			else:
				new_messages.append(m)
		self.messages = new_messages
		self.new_id()
		
		if self.conversation is not None:
			for m in removed_messages:
				self.conversation.message_removed(m)
			self.conversation.conversation_changed()
			
	def replace_message(self, old_message:Message, new_message:Message, keeping_latter:bool=False):
		found = False
		removed_messages = []
		
		if keeping_latter:
			try:
				old_message_index = self.messages.index(old_message)
				self.messages[old_message_index] = new_message
				if old_message_index>0:
					new_message.prev_message = self.messages[old_message_index-1]
				else:
					new_message.prev_message = None
				removed_messages.append(old_message)
				found = True
			except ValueError:
				pass
		else:
			new_messages = []
			for m in self.messages:
				if found:
					removed_messages.append(m)
				else:
					if m is old_message:
						found = True
						removed_messages.append(m)
					else:
						new_messages.append(m)
					
			if found:
				self.messages = new_messages
				self._add_message(new_message)
		
		if found:
			self.new_id()
			
			if self.conversation is not None:
				for m in removed_messages:
					self.conversation.message_removed(m)
				self.conversation.message_added(new_message)
				self.conversation.conversation_changed()
	
	def copy(self):
		new_sequence = MessageSequence()
		new_sequence.messages = self.messages[:]
		new_sequence.conversation = self.conversation
		new_sequence.new_id()
		return new_sequence
	
	def _add_message(self, message: Message):
		message.conversation = self.conversation
		
		if len(self.messages)>0:
			message.prev_message = self.messages[-1]
		self.messages.append(message)
		
	def __iter__(self):
		return iter(self.messages)
	
	def __getitem__(self, index):
		return self.messages[index]
	
	def __len__(self):
		return len(self.messages)
	
	def __contains__(self, message):
		return message in self.messages
	
	def index(self, message:Message) -> Optional[int]:
		'''
		Returns the index of message in this message sequence.
		
		Returns None if not found.
		'''
		for i, m in enumerate(self.messages):
			if m.auto_id == message.auto_id:
				return i
		return None
	
	def index_in(self, message_sequences:List["MessageSequence"]) -> Optional[int]:
		'''
		Returns the index of this message sequence in message_sequences.
		
		Returns None if not found.
		'''
		for i, ms in enumerate(message_sequences):
			if ms.auto_id == self.auto_id:
				return i
		return None
	
	
	@staticmethod
	def filter_sequences_for_next(message_sequences:List['MessageSequence'], filter_index:int, keep:'MessageSequence'=None):
		'''
		Return those message sequences who's message at filter_index is different.
		'''
		closed_set = {}
		filtered_sequences = []
		for ms in reversed(message_sequences):			
			if ms.messages is None or len(ms.messages) == 0:
				m = None
			elif filter_index is None:
				m = ms.messages[0].auto_id
			elif filter_index >= len(ms.messages):
				m = None
			else:
				m = ms.messages[filter_index].auto_id
				
			if keep is not None and ms.auto_id == keep.auto_id:
				if m in closed_set:
					filtered_sequences[closed_set[m]] = ms
				else:
					closed_set[m] = len(filtered_sequences)
					filtered_sequences.append(ms)
				continue
			
			if m is None:
				continue
			
			if m not in closed_set:
				closed_set[m] = len(filtered_sequences)
				filtered_sequences.append(ms)
		return filtered_sequences