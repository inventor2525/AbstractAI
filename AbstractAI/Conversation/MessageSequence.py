from AbstractAI.Conversation.ModelBase import *
from .Message import Message
from typing import List

@DATA
class MessageSequence:
	conversation: "Conversation"
	messages: List[Message] = field(default_factory=list)
		
	def add_message(self, message: Message):
		message.conversation = self.conversation
		
		if len(self.messages)>0:
			message.prev_message = self.messages[-1]
		self.messages.append(message)
		self.new_id()
		
	def remove_message(self, message: Message):
		self.messages.remove(message)
		self.new_id()
		
	def replace_message(self, old_message:Message, new_message:Message, keeping_latter:bool=False):
		if keeping_latter:
			try:
				self.messages[self.messages.index(old_message)] = new_message
			except ValueError:
				pass
		else:
			found = False
			new_messages = []
			for m in self.messages:
				if m is old_message:
					found = True
					break
				else:
					new_messages.append(m)
					
			if found:
				self.messages = new_messages
				self.add_message(new_message)
		self.new_id()