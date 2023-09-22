from enum import Enum
from .MessageSources.BaseMessageSource import BaseMessageSource, Hashable, hash_property
from datetime import datetime

from typing import Iterable, List

class Role(Enum):
	System = "system"
	User = "user"
	Assistant = "assistant"

class Message(Hashable):
	def __init__(self, content: str="", role: Role=Role.User, source: BaseMessageSource = None, prev_message:"Message"=None, conversation:"Conversation"=None):
		super().__init__()		
		self.creation_time = datetime.now()
		
		self.content = content
		self.role = role
			
		# Information about how the message was created and details about who/what created it
		self.source:BaseMessageSource = source
		
		self.prev_message = prev_message
		self.conversation = conversation
		self.hash_spoiled.add(self._hash_spoiled)
		
		self.children:List[Message] = []
		
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
	
	# @hash_property
	# def source(self, value: BaseMessageSource):
	# 	"""Information about how the message was created and details about who/what created it"""
	# 	pass
		
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
		
	@staticmethod	
	def expand_previous_messages(messages:Iterable["Message"]) -> Iterable["Message"]:
		'''
		Expands the previous_message property of each message
		in messages to include all previous messages, and returns
		the expanded list of messages from the earliest to the latest.
		'''
		all_messages = []
		closed_list = set()
		def in_closed_list(msg:Message) -> bool:
			if msg in closed_list:
				return True
			closed_list.add(msg)
			all_messages.append(msg)
			return False
			
		for message in messages:
			if in_closed_list(message):
				continue
			
			prev_message = message.prev_message
			while prev_message is not None:
				if in_closed_list(prev_message):
					break
				prev_message = prev_message.prev_message
		return reversed(all_messages)
	
	def create_edited(self, new_content:str) -> "Message":
		'''Create a new message that is an edited version of this message'''
		
		from .MessageSources.EditSource import EditSource
		source = EditSource(original=self)
		new_message = Message(
			new_content, self.role,
			source, self.prev_message, self.conversation
		)
		source.new = new_message
		return new_message