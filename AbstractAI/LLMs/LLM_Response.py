from AbstractAI.Model.Converse.Message import Message
from AbstractAI.Model.Converse.MessageSources import ModelSource
from typing import Callable, Iterator, Dict, Any
from dataclasses import dataclass

@dataclass
class LLM_Response:
	message:Message
	stop_streaming_func:Callable[[],None]
	
	@property
	def source(self) -> ModelSource:
		return self.message.source
	
	def stop(self):
		if self.stop_streaming_func:
			self.stop_streaming_func()
			self.stop_streaming_func = None
	
	def log_chunk(self, chunk:Dict[str,Any]):
		if "Chunks" not in self.source.serialized_raw_output:
			self.source.serialized_raw_output["Chunks"] = []
		self.source.serialized_raw_output["Chunks"].append(chunk)