from .LLM import *
from AbstractAI.LLMs.CommonRoles import CommonRoles
import tiktoken
from openai import OpenAI
from openai.types.chat import ChatCompletion, ChatCompletionChunk
import json
import os
#"gpt-3.5-turbo"

class OpenAI_LLM(LLM):
	def __init__(self, api_key:str, model_name:str, parameters:Dict[str, Any]={}):
		self.client = OpenAI(api_key=api_key)
		print(api_key)
		default = {
			"generate": {
				"temperature":0.2,
				"max_tokens":512
			}
		}
		super().__init__(model_name, merge_dictionaries(default, parameters))
	
	def _complete_str_into(self, prompt:str, message:Message, stream:bool=False) -> LLM_RawResponse:
		raise Exception("This doesn't support string prompts")
	
	def chat(self, conversation: Conversation, stream:bool=False) -> LLM_RawResponse:
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
		response = LLM_RawResponse(wip_message, 0, stream)
		
		completion = self.client.chat.completions.create(
			model=self.model_info.model_name,
			messages=message_list,
			**self.model_info.parameters["generate"],
			stream=stream
		)
		if stream:
			response.stop_streaming_func = completion.close
			def genenerate_more_func():
				try:
					next_response:ChatCompletionChunk = next(completion)
					if response.input_token_count == 0:
						try:
							in_tokens = tiktoken.encoding_for_model(next_response.model).encode(self._apply_chat_template(message_list))
							response.input_token_count = len(in_tokens)
							print(response.input_token_count)
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
		pass