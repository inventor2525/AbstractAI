from typing import List
from .Message import *

class Conversation:
	def __init__(self):
		self.messages:List[Message] = []

	def add_message(self, message: Message):
		self.messages.append(message)