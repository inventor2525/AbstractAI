from AbstractAI.Model.Converse.Message import Message
from AbstractAI.Model.Converse.MessageSources import ModelSource
from typing import Callable, Iterator, Dict, Any
from dataclasses import dataclass, field

@dataclass
class LLM_Response:
	message:Message
	stop_streaming_func:Callable[[],None] = None
	
	@property
	def source(self) -> ModelSource:
		return self.message.source
	
	def stop(self):
		if self.stop_streaming_func:
			self.stop_streaming_func()
			self.stop_streaming_func = None