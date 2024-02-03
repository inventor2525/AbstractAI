from AbstractAI.LLMs.CommonRoles import CommonRoles
from .LLM import *

from llama_cpp import Llama
from llama_cpp.llama_chat_format import LlamaChatCompletionHandlerRegistry, ChatFormatter, ChatFormatterResponse

class LLamaCPP_LLM(LLM):
	def __init__(self, model_name:str, model_path:str, parameters:Dict[str, Any]={}):
		default = {
			"tokenizer": {
				"use_fast": False,
				"trust_remote_code": True
			},
			"model": {
				"model_path": model_path,
				"n_ctx":2048,
				"n_threads":7,
				"n_gpu_layers":0,
				"chat_format":"llama-2"
			},
			"generate": {
				"max_tokens":1024,
				"stop": ["</s>"]
			}
		}
		super().__init__(model_name, merge_dictionaries(default, parameters))
		self.model = None
		
	def _load_model(self):
		self.model = Llama(**self.model_info.parameters["model"])
	
	def _complete_str_into(self, prompt: str, wip_message:Message, stream:bool=False) -> LLM_RawResponse:
		prompt_tokens = self.model.tokenize(prompt.encode("utf-8"), special=True) if prompt != "" else [self.model.token_bos()]
		completion = self.model.create_completion(prompt, **self.model_info.parameters["generate"], stream=stream)
		response = LLM_RawResponse(wip_message, len(prompt_tokens), stream)
		if not stream:
			response.set_response(completion['choices'][0]['text'], completion["usage"]["completion_tokens"], completion)
		else:
			def genenerate_more_func():
				try:
					next_response = next(completion)
					response.add_response_chunk(next_response['choices'][0]['text'], 1, next_response)
					return True
				except StopIteration:
					return False
			response.genenerate_more_func = genenerate_more_func
		return response
	
	def _apply_chat_template(self, conversation: Conversation, start_str:str="") -> str:
		chat = self.conversation_to_list(conversation)
		# The formatter functions in LlamaCPP are wrapped by the register_chat_format
		# decorator, which stores them in a registry of chat completion handlers with
		# no way to access them directly by name. So we have to do this to extract the
		# original function without something that performs the chat completion for us:
		formatter :ChatFormatter = LlamaChatCompletionHandlerRegistry().get_chat_completion_handler_by_name("llama-2").__closure__[0].cell_contents
		
		chat_formatted:ChatFormatterResponse = formatter(chat)
		return chat_formatted.prompt + start_str