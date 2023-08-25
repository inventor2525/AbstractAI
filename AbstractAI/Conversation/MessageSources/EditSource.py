from . import BaseMessageSource
from datetime import datetime

class EditSource(BaseMessageSource):
	"""A message source representing an edited message."""

	def __init__(self, original:"Message", new:"Message"):
		super().__init__()
		# A reference to the old version of the message
		self.original = original
		
		# A reference to the new version of the message
		self.new = new
		
	def recompute_hash(self):
		self._hash = self._compute_hash(self.original.hash, self.new.hash)