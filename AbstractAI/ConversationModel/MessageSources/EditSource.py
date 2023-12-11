from .BaseMessageSource import MessageSource
from AbstractAI.ConversationModel.ModelBase import *
from datetime import datetime

@DATA
class EditSource(MessageSource):
	"""A message source representing an edited message."""

	original: "Message"
	source_of_edit: MessageSource
	new: "Message" = None
	
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