from .MessageSource import MessageSource
from AbstractAI.ConversationModel.ModelBase import *
from AbstractAI.ConversationModel.ModelInfo import *
from AbstractAI.ConversationModel.MessageSequence import MessageSequence
from typing import Dict, Any, List, Union

@ConversationDATA
class ModelSource(MessageSource):
	'''Describes a message from a Large Language Model.'''
	model_info:ModelInfo
	message_sequence: MessageSequence = None
	prompt: str = None
	start_str: str = ""

	serialized_raw_output: Union[List[Dict[str,Any]], Dict[str,Any]] = field(default=list, compare=False)
	
	in_token_count: int = 0
	out_token_count: int = 0