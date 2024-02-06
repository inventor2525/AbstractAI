from AbstractAI.ConversationModel.Message import Message
from AbstractAI.Helpers.Signal import Signal
from typing import Dict, Any, List, Union, Callable
from dataclasses import dataclass, field

@dataclass
class LLM_RawResponse:
	message:Message
	input_token_count:int
	is_streamed:bool
	
	raw_response:Union[Dict[str, Any], List[Dict[str, Any]]] = field(default_factory=list)
	
	genenerate_more_func:Callable[[],bool] = None
	
	def set_response(self, text:str, out_token_count:int, raw_response:Dict[str, Any]):
		'''Used by the model to set the response of a blocking response.'''
		assert not self.is_streamed, "Set response is only for blocking responses. Use add_response_chunk for streamed responses."
		self.raw_response = raw_response
		self.message.source.in_token_count = self.input_token_count
		self.message.source.out_token_count = out_token_count
		
		self.message.content = text
		self.message.changed(self.message)
		
	def add_response_chunk(self, text:str, out_token_count:int, response_chunk:Dict[str, Any]):
		'''Used by the model to add a response chunk to a streamed response.'''
		assert self.is_streamed, "Add response chunk is only for streamed responses. Use set_response for blocking responses."
		self.raw_response.append(response_chunk)
		self.message.source.in_token_count = self.input_token_count
		self.message.source.out_token_count += out_token_count
		
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
		return self.genenerate_more_func()