from enum import Enum
from .MessageSources import BaseMessageSource, UserSource, ModelSource, EditSource, TerminalSource
from AbstractAI.Hashable import Hashable
from datetime import datetime

class Role(Enum):
	System = "system"
	User = "user"
	Assistant = "assistant"

class Message(Hashable):
	def __init__(self, content: str, role: Role, source: BaseMessageSource = None, prev_message:"Message"=None, conversation:"Conversation"=None):
		super().__init__()
		
		# The date time the message was created
		self.creation_time: datetime = datetime.now()
		
		# The text of the message
		self.content = content
		
		# Who the message came from
		self.role = role
		
		# Information about how the message was created and details about who/what created it
		self.source = source
		
		# The message that comes before this in the full tree of a conversation and all the paths it can evolve from. (Not to be confused with "Conversation" which is a single linear string of messages)
		self.prev_message = prev_message
		
		# A weak reference back to the conversation this message is apart of
		self.conversation = conversation
		
	def recompute_hash(self):
		self._hash = self._compute_hash((
			self.creation_time, 
			self.content, self.role,
			self.source.hash if self.source else None,
			self.prev_message.hash if self.prev_message else None,
			self.conversation.hash if self.conversation else None
		))