from AbstractAI.ConversationModel import *
from ClassyFlaskDB.DATA import DATAEngine
from AbstractAI.Helpers.Signal import Signal
from dataclasses import dataclass, field
from typing import List, Union
import pytz

from copy import deepcopy
@dataclass
class ConversationCollection():
	conversations: List[Conversation] = field(default_factory=list)
	engine : DATAEngine = None
	
	conversation_added: Signal[[Conversation], None] = Signal.field()
	
	def _register_conversation(self, conversation:Conversation) -> None:
		def message_changed(message):
			self.engine.merge(message)
			
		def message_added(message):
			self.engine.merge(message)
			message.changed.connect(message_changed, auto_disconnect=True)
		conversation.message_added.connect(message_added)
		
		def conversation_changed(conversation):
			self.engine.merge(conversation)
		conversation.conversation_changed.connect(lambda conversation=conversation: conversation_changed(conversation))
			
	def append(self, conversation:Conversation, should_notify=True) -> None:
		self.conversations.append(conversation)
		self._register_conversation(conversation)
		if should_notify:
			self.conversation_added(conversation)
	
	@classmethod
	def all_from_engine(cls, engine: DATAEngine) -> 'ConversationCollection':
		collection = cls()
		with engine.session() as session:
			all_conversations = session.query(Conversation.auto_id, Conversation.name, Conversation.description, Conversation.creation_time__DateTimeObj, Conversation.creation_time__TimeZone, Conversation.last_modified__DateTimeObj, Conversation.last_modified__TimeZone).all()
			for conversation_fields in all_conversations:
				auto_id, name, description, creation_time, creation_timezone, last_modified, last_modified_timezone = deepcopy(conversation_fields)
				if creation_timezone is not None:
					creation_time.replace(tzinfo=pytz.timezone(creation_timezone))
				if last_modified_timezone is not None:
					last_modified.replace(tzinfo=pytz.timezone(last_modified_timezone))
				conversation = Conversation(name, description, creation_time, last_modified, None)
				conversation.auto_id = auto_id
				
				collection.conversations.append(conversation)
			collection.engine = engine
		return collection

	def load_completely(self, conversation:Union[int, Conversation]) -> Conversation:
		if isinstance(conversation, int):
			conversation_index = conversation
			conversation = self.conversations[conversation]
		else:
			conversation_index = self.conversations.index(conversation)
		
		if conversation.message_sequence is None:
			with self.engine.session() as session:
				conversations_message_sequences = deepcopy(session.query(MessageSequence).filter(MessageSequence.conversation_fk == conversation.auto_id).all())
				if len(conversations_message_sequences) == 0:
					whole_conversation = deepcopy(session.query(Conversation).filter(Conversation.auto_id == conversation.auto_id).first())
				else:
					whole_conversation = conversations_message_sequences[0].conversation
				self.conversations[conversation_index] = whole_conversation
				self._register_conversation(whole_conversation)
				return whole_conversation
		else:
			return conversation
	
	def __iter__(self):
		return iter(self.conversations)
	
	def __getitem__(self, index):
		return self.conversations[index]
	
	def __len__(self):
		return len(self.conversations)
	
	def __contains__(self, conversation):
		return conversation.auto_id in (c.auto_id for c in self.conversations)
	
	def __delitem__(self, index):
		del self.conversations[index]
		#TODO: notify
	
	def __setitem__(self, index, conversation):
		self.conversations[index] = conversation
		#TODO: notify