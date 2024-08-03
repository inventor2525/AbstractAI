from AbstractAI.LLMs.LLM import LLM
from AbstractAI.Model.Converse import Conversation, Message, Role
from AbstractAI.Model.Settings.OpenAI_LLMSettings import OpenAI_LLMSettings
from AbstractAI.Model.Converse.MessageSources import ModelSource
import tiktoken
from openai import OpenAI
from openai.types.chat import ChatCompletion, ChatCompletionChunk
from openai._streaming import Stream
import json
import os
from typing import List, Dict, Any

class OpenAI_LLM(LLM):
	def __init__(self, settings:OpenAI_LLMSettings):
		self.client = None
		super().__init__(settings)
	
	def chat(self, conversation: Conversation, start_str:str="", stream:bool=False, max_tokens:int=None) -> Message:
		wip_message, message_list = self._new_message(conversation, start_str)
		
		completion:ChatCompletion|Stream[ChatCompletionChunk] = self.client.chat.completions.create(
			model=self.settings.model_name,
			messages=message_list,
			max_tokens=max_tokens,
			# temperature=self.settings.temperature,
			stream=stream
		)
		
		if stream:
			chunk_iterator = iter(completion)

			def continue_function():
				try:
					chunk = next(chunk_iterator)
					if chunk.choices[0].delta.content:
						if wip_message.append(chunk.choices[0].delta.content):
							wip_message.source.out_token_count += 1
					self._log_chunk(self._dict_from_obj(chunk), wip_message)
					wip_message.source.finished = chunk.choices[0].finish_reason == 'stop'
					return True
				except StopIteration:
					wip_message.source.generating = False
					wip_message.source.finished = True
					return False

			wip_message.source.continue_function = continue_function
			wip_message.source.stop_function = completion.close
		else:
			wip_message.content = completion.choices[0].message.content
			wip_message.source.finished = completion.choices[0].finish_reason == 'stop'
			wip_message.source.serialized_raw_output = self._dict_from_obj(completion)
			
			if completion.usage:
				wip_message.source.in_token_count = completion.usage.prompt_tokens
				wip_message.source.out_token_count = completion.usage.completion_tokens

			wip_message.source.generating = False

		return wip_message
	
	def _apply_chat_template(self, chat: List[Dict[str,str]], start_str:str="") -> str:
		if start_str is not None and len(start_str) > 0:
			raise Exception("Start string not supported by OpenAI")
		prompt_peices = []
		for message in chat:
			prompt_peices.append( f"#{message['role']}:\n{message['content']}" )
		return "\n\n".join(prompt_peices)
	
	def _load_model(self):
		self.client = OpenAI(api_key=self.settings.api_key)
	
	def count_tokens(self, text:str, model_name:str=None) -> int:
		'''Count the number of tokens in the passed text.'''
		if model_name is None:
			model_name = self.settings.model_name
		try:
			return len(tiktoken.encoding_for_model(model_name).encode(text))
		except:
			return -1