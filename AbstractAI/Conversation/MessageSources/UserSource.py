from .BaseMessageSource import BaseMessageSource, hash_property

class UserSource(BaseMessageSource):
	"""Describes the source of a message from a person."""

	def __init__(self, user_name: str = "user"):
		super().__init__()
		self.user_name = user_name
		
	@hash_property
	def user_name(self, value: str):
		"""The user name of who wrote the message"""
		pass