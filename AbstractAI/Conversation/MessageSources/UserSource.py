from AbstractAI.Conversation.ModelBase import *
from .BaseMessageSource import MessageSource

@DATA
class UserSource(MessageSource):
	'''Describes the source of a message from a person.'''
	user_name: str
	session_start_time: datetime = field(default_factory=get_local_time)