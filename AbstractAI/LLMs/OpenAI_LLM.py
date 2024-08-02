from .LLM import *
from AbstractAI.Helpers.dict_from_obj import dict_from_obj
import tiktoken
from openai import OpenAI
from openai.types.chat import ChatCompletion, ChatCompletionChunk
from openai._streaming import Stream
import json
import os
from AbstractAI.Model.Settings.OpenAI_LLMSettings import OpenAI_LLMSettings

class OpenAI_LLM(LLM):
	def __init__(self, settings:OpenAI_LLMSettings):
		self.client = None
		super().__init__(settings)
	
	def chat(self, conversation: Conversation, start_str:str="", stream=False, max_tokens:int=None) -> Union[LLM_Response, Iterator[LLM_Response]]:
		wip_message, message_list = self._new_message(conversation, start_str, default_start_request_prompt)
		
		completion:ChatCompletion|Stream[ChatCompletionChunk] = self.client.chat.completions.create(
			model=self.settings.model_name,
			messages=message_list,
			max_tokens=max_tokens,
			# temperature=self.settings.temperature,
			stream=stream
		)
		
		if stream:
			response = LLM_Response(wip_message, completion.close)
			yield response
			
			for i, chunk in enumerate(completion):
				if response.message.append(chunk.choices[0].delta.content):
					response.source.out_token_count += 1
				self._log_chunk(dict_from_obj(chunk), wip_message)
				response.source.finished = chunk.choices[0].finish_reason == 'stop'
				yield response
			response.source.generating = False
		else:
			response.source.finished = completion.choices[0].finish_reason == 'stop'
			response.message.content = completion.choices[0].message.content
			response.source.in_token_count = completion.usage.prompt_tokens
			response.source.out_token_count = completion.usage.completion_tokens
			response.source.serialized_raw_output = dict_from_obj(completion)
			response.source.generating = False
		
		return response
	
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