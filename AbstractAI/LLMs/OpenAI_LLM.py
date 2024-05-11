from .LLM import *
from AbstractAI.LLMs.CommonRoles import CommonRoles
import tiktoken
from openai import OpenAI
from openai.types.chat import ChatCompletion, ChatCompletionChunk
import json
import os
from AbstractAI.Settings.OpenAI_LLMSettings import OpenAI_LLMSettings

class OpenAI_LLM(LLM):
	def __init__(self, settings:OpenAI_LLMSettings):
		self.client = None
		super().__init__(settings)
	
	def _complete_str_into(self, prompt:str, message:Message, stream:bool=False, max_tokens:int=None) -> LLM_Response:
		raise Exception("This doesn't support string prompts")
	
	def chat(self, conversation: Conversation, start_str:str="", stream=False, max_tokens:int=None) -> LLM_Response:
		'''
		Prompts the model with a Conversation using a blocking method
		and creates a LLM_RawResponse from what it returns.
		'''
		def deep_object_to_dict(obj):
			"""
			Recursively convert an object and all nested objects to dictionaries.
			"""
			if isinstance(obj, dict):
				return {k: deep_object_to_dict(v) for k, v in obj.items()}
			elif isinstance(obj, (list, tuple, set)):
				return [deep_object_to_dict(item) for item in obj]
			elif not isinstance(obj, (str, int, float, bool)) and hasattr(obj, "__dict__"):
				return {k: deep_object_to_dict(v) for k, v in obj.__dict__.items()}
			else:
				return obj
		message_list = self.conversation_to_list(conversation)
		wip_message = self._new_message(json.dumps(message_list, indent=4), conversation, "")
		response = LLM_Response(wip_message, 0, stream)
		
		completion = self.client.chat.completions.create(
			model=self.settings.model_name,
			messages=message_list,
			max_tokens=max_tokens,
			temperature=self.settings.temperature,
			stream=stream
		)
		if stream:
			response.stop_streaming_func = completion.close
			def genenerate_more_func():
				try:
					next_response:ChatCompletionChunk = next(completion)
					if response.input_token_count == 0:
						try:
							response.input_token_count = self.count_tokens(self._apply_chat_template(message_list), next_response.model)
						except Exception as e:
							print(e)
					content = next_response.choices[0].delta.content
					has_content = content is not None and len(content) > 0
					response.add_response_chunk(content, 1 if has_content else 0, deep_object_to_dict(next_response))
					return True
				except StopIteration:
					return False
			#response_tokens = self.encoding.encode(response_text)
			response.genenerate_more_func = genenerate_more_func
			response.input_token_count = 0
		else:
			response.input_token_count = completion.usage.prompt_tokens
			response.set_response(completion.choices[0].message.content, completion.usage.completion_tokens, deep_object_to_dict(completion))
		
		return response
	
	def _apply_chat_template(self, chat: List[Dict[str,str]], start_str:str="") -> str:
		if start_str is not None and len(start_str) > 0:
			raise Exception("Start string not supported by OpenAI")
		prompt_peices = []
		for message in chat:
			prompt_peices.append( f"#{message['role']}:\n{message['content']}" )
		return "\n\n".join(prompt_peices)
	
	def _load_model(self):
		self.client = OpenAI(api_key=self.api_key)
	
	def count_tokens(self, text:str, model_name:str=None) -> int:
		'''Count the number of tokens in the passed text.'''
		if model_name is None:
			model_name = self.settings.model_name
		return len(tiktoken.encoding_for_model(model_name).encode(text))