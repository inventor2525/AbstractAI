from . import BaseMessageSource

class EditSource(BaseMessageSource):
	"""A message source representing an edited message."""

	def __init__(self, original:"Message"):
		super().__init__()
		# A reference to the version of the message this one is edited from
		self.original = original
		
	def recompute_hash(self):
		self.hash = self._compute_hash(self.original.hash)