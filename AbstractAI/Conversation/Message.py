from enum import Enum
from .MessageSources.BaseMessageSource import BaseMessageSource, Hashable, hash_property
from datetime import datetime

class Role(Enum):
	System = "system"
	User = "user"
	Assistant = "assistant"

class Message(Hashable):
	def __init__(self, content: str, role: Role, source: BaseMessageSource = None, prev_message:"Message"=None, conversation:"Conversation"=None):
		super().__init__()		
		self.creation_time = datetime.now()
		self.content = content
		self.role = role
		self.source = source
		self.prev_message = prev_message
		self.conversation = conversation
		self.hash_spoiled.add(self._hash_spoiled)
		
	@hash_property
	def creation_time(self, value: datetime):
		"""The date time the message was created"""
		pass
		
	@hash_property
	def content(self, value: str):
		"""The text of the message"""
		pass
		
	@hash_property
	def role(self, value: Role):
		"""Who the message came from"""
		pass
		
	@hash_property
	def source(self, value: BaseMessageSource):
		"""Information about how the message was created and details about who/what created it"""
		pass
		
	@hash_property
	def prev_message(self, value: "Message"):
		"""The message that comes before this in the full tree of a conversation and all the paths it can evolve from. (Not to be confused with "Conversation" which is a single linear string of messages)"""
		pass
		
	@hash_property
	def conversation(self, value: "Conversation"):
		"""A weak reference back to the conversation this message is apart of"""
		pass
	
	def _hash_spoiled(self):
		if self.conversation is not None:
			self.conversation.spoil_hash()