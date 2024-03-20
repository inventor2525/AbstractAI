from AbstractAI.ConversationModel.ModelBase import *
from .MessageSource import MessageSource

DefaultUser = "User"

@ConversationDATA
class UserSource(MessageSource):
	'''Describes the source of a message from a person.'''
	user_name: str = DefaultUser
	session_start_time: datetime = field(default_factory=get_local_time)