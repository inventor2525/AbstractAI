from .MessageSource import MessageSource
from AbstractAI.ConversationModel.ModelBase import *

@DATA
class TerminalSource(MessageSource):
	"""
	Describes the source of a message from a terminal command result.
	
	Messages with this source came from the terminal result of
	running a command.
	"""
	command: str
	un_parsed_output: str = None