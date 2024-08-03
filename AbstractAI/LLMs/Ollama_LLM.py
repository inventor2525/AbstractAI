from AbstractAI.LLMs.LLM import *
from AbstractAI.Model.Converse import Conversation, Message, Role
from AbstractAI.Model.Settings.Ollama_LLMSettings import Ollama_LLMSettings
from AbstractAI.Model.Converse.MessageSources import ModelSource
import ollama
from typing import List, Dict, Any

class Ollama_LLM(LLM):
	def __init__(self, settings:Ollama_LLMSettings):
		self.client = None
		super().__init__(settings)
	
	def chat(self, conversation: Conversation, start_str:str="", stream:bool=False, max_tokens:int=None) -> Message:
		wip_message, message_list = self._new_message(conversation, start_str)
		
		completion = ollama.chat(
			model=self.settings.model_name,
			messages=message_list,
			stream=stream
		)
		
		if stream:
			chunk_iterator = iter(completion)

			def continue_function():
				try:
					chunk = next(chunk_iterator)
					if wip_message.source.out_token_count > max_tokens-1:
						self.stop_message(wip_message)
					if wip_message.append(chunk['message']['content']):
						wip_message.source.out_token_count += 1
					self._log_chunk(chunk, wip_message)
					wip_message.source.finished = chunk.get('done_reason', False)
					return True
				except StopIteration:
					wip_message.source.generating = False
					wip_message.source.finished = True
					return False

			wip_message.source.continue_function = continue_function
			wip_message.source.stop_function = lambda: None  # Ollama doesn't provide a stop function
		else:
			wip_message.content = completion['message']['content']
			wip_message.source.finished = True
			wip_message.source.serialized_raw_output = completion
			wip_message.source.out_token_count = completion.get('eval_count', 0)
			wip_message.source.generating = False

		return wip_message