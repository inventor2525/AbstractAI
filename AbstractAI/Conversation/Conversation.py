from typing import List
from .Message import Message
from AbstractAI.Hashable import Hashable, hash_property
from .MessageSequence import MessageSequence
from datetime import datetime

class Conversation(Hashable):
	'''A list of messages that can be passed to a Large Language Model'''
	def __init__(self, name:str="", description:str="", creation_time:datetime=datetime.now()):
		super().__init__()
		self.creation_time = creation_time
		
		self.name = name
		self.description = description
		self.message_sequence = MessageSequence()
	
	@hash_property
	def creation_time(self, value: datetime):
		"""The description of the conversation."""
		pass
	
	# @hash_property
	# def name(self, value: str):
	# 	"""The name of the conversation."""
	# 	pass
	
	# @hash_property
	# def description(self, value: str):
	# 	"""The description of the conversation."""
	# 	pass