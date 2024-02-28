from AbstractAI.ConversationModel.Message import Message
from AbstractAI.Helpers.Signal import Signal
from typing import Dict, Any, List, Union, Callable
from dataclasses import dataclass, field

@dataclass
class LLM_Response:
	message:Message
	input_token_count:int
	is_streamed:bool
	
	raw_response:Union[Dict[str, Any], List[Dict[str, Any]]] = field(default_factory=list)
	
	genenerate_more_func:Callable[[],bool] = None
	stop_streaming_func:Callable[[],None] = None
	
	def __post_init__(self):
		self.message.source.generating = True

	def set_response(self, text:str, out_token_count:int, raw_response:Dict[str, Any]):
		'''Used by the model to set the response of a blocking response.'''
		assert not self.is_streamed, "Set response is only for blocking responses. Use add_response_chunk for streamed responses."
		self.raw_response = raw_response
		self.message.source.serialized_raw_output = raw_response
		self.message.source.in_token_count = self.input_token_count
		self.message.source.out_token_count = out_token_count
		self.message.source.finished = True
		self.message.source.generating = False
		print("dn!")
		
		self.message.content = text
		
	def add_response_chunk(self, text:str, out_token_count:int, response_chunk:Dict[str, Any]):
		'''Used by the model to add a response chunk to a streamed response.'''
		assert self.is_streamed, "Add response chunk is only for streamed responses. Use set_response for blocking responses."
		self.raw_response.append(response_chunk)
		
		if "Chunks" not in self.message.source.serialized_raw_output:
			self.message.source.serialized_raw_output["Chunks"] = []
		self.message.source.serialized_raw_output["Chunks"].append(response_chunk)
		
		self.message.source.in_token_count = self.input_token_count
		self.message.source.out_token_count += out_token_count
		self.message.source.finished = False
		
		if text is not None:
			self.message.content += text
		self.message.changed(self.message)
	
	def generate_more(self) -> bool:
		'''
		Call this to get the next response chunk from the model.
		
		Calling this will update the message content and token counts
		with changed notifications, and return if there are more chunks.
		'''
		assert self.is_streamed, "Next is only for streamed responses."
		assert self.genenerate_more_func is not None, "genenerate_more_func not set. This should have been done by the model."
		has_more = self.genenerate_more_func()
		if not has_more:
			self.message.source.finished = True
			self.message.source.generating = False
			print("donne!")
		return has_more
	
	def stop_streaming(self):
		'''Call this to stop streaming and close the connection.'''
		assert self.is_streamed, "Stop streaming is only for streamed responses."
		if self.stop_streaming_func is not None:
			self.stop_streaming_func()
		self.message.source.generating = False
		self.message.changed(self.message)
		print("stp!")
	
	def copy_from(self, other:Message):
		'''Copy the response data from another message.'''
		self.message.content = other.content
		self.message.source.serialized_raw_output = other.source.serialized_raw_output
		self.message.source.in_token_count = other.source.in_token_count
		self.message.source.out_token_count = other.source.out_token_count
		self.message.source.finished = other.source.finished
		self.message.changed(self.message)