from AbstractAI.ConversationModel.ModelBase import *
from .Message import Message
from typing import List

@ConversationDATA(generated_id_type=ID_Type.HASHID, hashed_fields=["messages"])
class MessageSequence:
	messages: List[Message] = field(default_factory=list)
	conversation: "Conversation" = field(default=None, compare=False)
	
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
	
	def copy(self):
		new_sequence = MessageSequence()
		new_sequence.messages = self.messages[:]
		new_sequence.conversation = self.conversation
		new_sequence.new_id()
		return new_sequence
	
	def __iter__(self):
		return iter(self.messages)
	
	def __getitem__(self, index):
		return self.messages[index]
	
	def __len__(self):
		return len(self.messages)
	
	def __contains__(self, message):
		return message in self.messages
	
	#TODO better follow collection pattern for other methods above