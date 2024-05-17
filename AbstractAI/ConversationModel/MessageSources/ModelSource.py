from .MessageSource import MessageSource
from AbstractAI.ConversationModel.ModelBase import *
from AbstractAI.ConversationModel.ModelInfo import *
from AbstractAI.ConversationModel.MessageSequence import MessageSequence
from typing import Dict, Any, List, Union

@DATA
@dataclass
class ModelSource(MessageSource):
	'''Describes a message from a Large Language Model.'''
	model_class: str = None
	settings:"LLMSettings" = None
	message_sequence: MessageSequence = None
	prompt: str = None
	start_str: str = ""
	model_info:ModelInfo=None #This is a legacy field that is no longer used, here only to support legacy database entries and can be removed completely and safely for new users

	serialized_raw_output: Dict[str,Any] = field(default_factory=dict, compare=False)
	
	in_token_count: int = 0
	out_token_count: int = 0
	finished: bool = False