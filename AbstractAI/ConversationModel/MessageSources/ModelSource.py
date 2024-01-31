from .MessageSource import MessageSource
from AbstractAI.ConversationModel.ModelBase import *
from AbstractAI.ConversationModel.ModelInfo import *
from AbstractAI.ConversationModel.MessageSequence import MessageSequence
from typing import Dict, Any

@ConversationDATA
class ModelSource(MessageSource):
	'''Describes a message from a Large Language Model.'''
	model_info:ModelInfo
	message_sequence: MessageSequence = None
	prompt: str = None
	start_str: str = ""

	serialized_raw_output: Dict[str,Any] = field(default=None, compare=False)