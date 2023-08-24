from . import BaseMessageSource
from AbstractAI.Conversation.Message import Message

class EditSource(BaseMessageSource):
	"""A message source representing an edited message."""

	def __init__(self, original:Message):
		super().__init__()
		# A reference to the version of the message this one is edited from
		self.original = original