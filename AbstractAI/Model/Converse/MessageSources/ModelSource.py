from ClassyFlaskDB.DefaultModel import *
from AbstractAI.Model.Converse.MessageSequence import MessageSequence
from AbstractAI.Model.Settings.LLMSettings import LLMSettings
from typing import Dict, Any, List, Union

@DATA
@dataclass
class ModelSource(Object):
	'''Describes a message from a Large Language Model.'''
	settings:LLMSettings = None
	message_sequence: MessageSequence = None
	prompt: str = None
	start_str: str = ""
	
	serialized_raw_output: Dict[str,Any] = field(default_factory=dict, compare=False)
	
	in_token_count: int = -1
	out_token_count: int = 0
	finished: bool = False