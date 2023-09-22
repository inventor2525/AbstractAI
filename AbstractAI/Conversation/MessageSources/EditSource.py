from .BaseMessageSource import BaseMessageSource, hash_property
from AbstractAI.Conversation.Message import Message
from datetime import datetime

class EditSource(BaseMessageSource):
	"""A message source representing an edited message."""

	def __init__(self, original:"Message"=None, new:"Message"=None):
		super().__init__()
		self.original = original
		self.new = new
	
	@staticmethod
	def most_original(source:"EditSource") -> "Message":
		"""Returns the most original message in the edit chain"""
		
		if source is None:
			return None
			
		prev = source.original
		while prev is not None and prev.source is not None:
			if isinstance(prev.source, EditSource):
				prev = prev.source.original
			else:
				break
			
		return prev
	
	@hash_property
	def original(self, value:"Message"):
		'''A reference to the old version of the message'''
		pass
	
	@hash_property
	def new(self, value:"Message"):
		'''A reference to the new version of the message'''
		pass