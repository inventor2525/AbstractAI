from AbstractAI.ConversationModel import *
from ClassyFlaskDB.DATA import DATAEngine
from AbstractAI.Helpers.Signal import Signal
from dataclasses import dataclass, field
from typing import List

from copy import deepcopy
@dataclass
class ConversationCollection():
	conversations: List[Conversation] = field(default_factory=list)
	engine : DATAEngine = None
	
	conversation_added: Signal[[Conversation], None] = Signal.field()
				
	def append(self, conversation:Conversation, should_notify=True) -> None:
		self.conversations.append(conversation)
		conversation.message_added.connect(lambda message: self.engine.merge(message.conversation))
		if should_notify:
			self.conversation_added(conversation)
	
	@classmethod
	def all_from_engine(cls, engine:DATAEngine) -> None:
		collection = cls()
		
		with engine.session() as session:
			all_conversations = deepcopy(session.query(Conversation).order_by(Conversation.creation_time__DateTimeObj).all())
			
			for conversation in all_conversations:
				collection.append(conversation, should_notify=False)
		
		collection.engine = engine
		return collection
	
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