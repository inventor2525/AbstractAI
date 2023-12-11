from enum import Enum
from AbstractAI.ConversationModel.ModelBase import *
from .MessageSources import MessageSource, UserSource, ModelSource, EditSource
from .MessageSources.EditSource import EditSource
from datetime import datetime

from typing import Iterable, List, Union

class Role(Enum):
	System = "system"
	User = "user"
	Assistant = "assistant"
	
@DATA
class Message:
	content: str
	source: MessageSource = None
	
	creation_time: datetime = field(default_factory=get_local_time)
	
	prev_message: "Message" = None
	conversation: "Conversation" = None
	
	_children: List["Message"] = field(default_factory=list)

	@staticmethod	
	def expand_previous_messages(messages:Iterable["Message"]) -> Iterable["Message"]:
		'''
		Expands the previous_message property of each message
		in messages to include all previous messages, and returns
		the expanded list of messages from the earliest to the latest.
		'''
		all_messages = []
		closed_list = set()
		def in_closed_list(msg:Message) -> bool:
			if msg in closed_list:
				return True
			closed_list.add(msg)
			all_messages.append(msg)
			return False
			
		for message in messages:
			if in_closed_list(message):
				continue
			
			prev_message = message.prev_message
			while prev_message is not None:
				if in_closed_list(prev_message):
					break
				prev_message = prev_message.prev_message
		return reversed(all_messages)
	
	def create_edited(self, new_content:str, source_of_edit:Union[UserSource, "ModelSource"]=None) -> "Message":
		'''Create a new message that is an edited version of this message'''
		
		source = EditSource(original=self, source_of_edit=source_of_edit)
		new_message = Message(new_content, source)
		new_message.prev_message = self.prev_message
		new_message.conversation = self.conversation
		source.new = new_message
		return new_message