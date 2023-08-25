from typing import List
from .Message import *
from AbstractAI.Hashable import Hashable
from .MessageSequence import MessageSequence
from datetime import datetime

class Conversation(Hashable):
	'''A list of messages that can be passed to a Large Language Model'''
	def __init__(self, name:str="", description:str="", creation_time:datetime=datetime.now()):
		super().__init__()
		self.name = name
		self.description = description
		self.creation_time = creation_time
		self.message_sequence = MessageSequence()
		
	def recompute_hash(self):
		self._hash = self._compute_hash((self.creation_time))