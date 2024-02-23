from AbstractAI.ConversationModel import *
from ClassyFlaskDB.DATA import DATAEngine
from AbstractAI.Helpers.Signal import Signal
from dataclasses import dataclass, field
from typing import List
import pytz

from copy import deepcopy
@dataclass
class ConversationCollection():
	conversations: List[Conversation] = field(default_factory=list)
	engine : DATAEngine = None
	
	conversation_added: Signal[[Conversation], None] = Signal.field()
				
	def append(self, conversation:Conversation, should_notify=True) -> None:
		self.conversations.append(conversation)
		def message_added(message):
			self.engine.merge(message.conversation)
			def message_changed(message):
				self.engine.merge(message)
			message.changed.connect(message_changed)
		conversation.message_added.connect(message_added)
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
				
				def get_message_sequence(self):
					if hasattr(self, "message_sequence") and self.message_sequence is not None:
						return self.message_sequence
					ms = collection._load_completely(self)
					setattr(self, "message_sequence", ms)
					return ms
				setattr(conversation, 'get_message_sequence', lambda self=conversation: get_message_sequence(self))
				collection.append(conversation, should_notify=False)
			collection.engine = engine
		return collection

	def _load_completely(self, conversation:Conversation):
		with self.engine.session() as session:
			conversation = session.query(Conversation).filter(Conversation.auto_id == conversation.auto_id).first()
			return conversation.message_sequence
	
	def __iter__(self):
		return iter(self.conversations)
	
	def __getitem__(self, index):
		return self.conversations[index]
	
	def __len__(self):
		return len(self.conversations)
	
	def __contains__(self, conversation):
		return conversation in self.conversations
	
	def __delitem__(self, index):
		del self.conversations[index]
		#TODO: notify
	
	def __setitem__(self, index, conversation):
		self.conversations[index] = conversation
		#TODO: notify