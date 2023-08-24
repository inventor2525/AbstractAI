from . import BaseMessageSource

class UserSource(BaseMessageSource):
	"""Describes the source of a message from a person."""

	def __init__(self, user_name: str = "user"):
		super().__init__()
		# The user name of who wrote the message
		self.user_name: str = user_name