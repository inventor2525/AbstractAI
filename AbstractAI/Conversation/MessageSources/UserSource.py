from . import BaseMessageSource, hash_property

class UserSource(BaseMessageSource):
	"""Describes the source of a message from a person."""

	def __init__(self, user_name: str = "user"):
		super().__init__()
		# The user name of who wrote the message
		self.user_name: str = user_name
		
	def recompute_hash(self):
		self._hash = self._compute_hash(self.user_name)