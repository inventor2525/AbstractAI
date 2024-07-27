from AbstractAI.Model.Converse import *
from ClassyFlaskDB.new.SQLStorageEngine import SQLStorageEngine
from AbstractAI.Helpers.Signal import Signal
from dataclasses import dataclass, field
from typing import List, Union, Dict

from datetime import datetime
from dateutil import tz
import tzlocal

from copy import deepcopy
@dataclass
class ConversationCollection():
	conversations: List[Conversation] = field(default_factory=list)
	engine : SQLStorageEngine = None
	
	conversation_added: Signal[[Conversation], None] = Signal.field()
	
	def __post_init__(self):
		for index, conversation in enumerate(self.conversations):
			self._register_conversation(conversation)
	
	def _register_conversation(self, conversation:Conversation) -> None:
		if self.engine is None:
			return
		
		def message_changed(message):
			self.engine.merge(message, merge_depth_limit=2)
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
	
	def get_conversation(self, conv_id:str) -> Conversation:
		conv = self.engine.query(Conversation).filter_by_id(conv_id)
		if conv:
			return conv
		for conv in self.conversations:
			if conv.get_primary_key() == conv_id:
				return conv
		return None
	
	@classmethod
	def all_from_engine(cls, engine: SQLStorageEngine) -> 'ConversationCollection':
		collection = cls()
		collection.conversations = list(engine.query(Conversation).all())
		collection.engine = engine
			
		return collection
	
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