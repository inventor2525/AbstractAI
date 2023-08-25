from .BaseMessageSource import BaseMessageSource, hash_property
from datetime import datetime

class EditSource(BaseMessageSource):
	"""A message source representing an edited message."""

	def __init__(self, original:"Message", new:"Message"):
		super().__init__()
		self.original = original
		self.new = new
		
	@hash_property
	def original(self, value:"Message"):
		'''A reference to the old version of the message'''
		pass
	
	@hash_property
	def new(self, value:"Message"):
		'''A reference to the new version of the message'''
		pass