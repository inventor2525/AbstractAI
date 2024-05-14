from AbstractAI.LLMs.CommonRoles import CommonRoles
from .LLM import *

from llama_cpp import Llama
from llama_cpp.llama_chat_format import LlamaChatCompletionHandlerRegistry, ChatFormatter, ChatFormatterResponse
from AbstractAI.Settings.LLamaCpp_LLMSettings import LLamaCpp_LLMSettings

class LLamaCPP_LLM(LLM):
	def __init__(self, settings:LLamaCpp_LLMSettings):
		super().__init__(settings)
		self.model = None
		
	def _load_model(self):
		self.model = Llama(
			self.settings.model.model_path,
			n_ctx=self.settings.model.n_ctx,
			n_gpu_layers=self.settings.model.n_gpu_layers,
			n_threads=self.settings.model.n_threads,
			main_gpu=self.settings.model.main_gpu,
			chat_format=self.settings.model.chat_format,
			flash_attn=self.settings.model.flash_attn,
			verbose=self.settings.model.verbose
		)
	
	def _complete_str_into(self, prompt: str, wip_message:Message, stream:bool=False, max_tokens:int=None) -> LLM_Response:
		params = kwargs_from_instance(self.model.create_completion, self.settings.generate)
		
		if max_tokens is not None:
			params["max_tokens"] = max_tokens
		print(params)
		completion = self.model.create_completion(prompt, **params, stream=stream)
		response = LLM_Response(wip_message, self.count_tokens(prompt), stream)
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
	
	def _apply_chat_template(self, chat: List[Dict[str,str]], start_str:str="") -> str:
		# The formatter functions in LlamaCPP are wrapped by the register_chat_format
		# decorator, which stores them in a registry of chat completion handlers with
		# no way to access them directly by name. So we have to do this to extract the
		# original function without something that performs the chat completion for us:
		formatter :ChatFormatter = LlamaChatCompletionHandlerRegistry().get_chat_completion_handler_by_name("llama-2").__closure__[0].cell_contents
		
		chat_formatted:ChatFormatterResponse = formatter(chat)
		return chat_formatted.prompt + start_str
	
	def count_tokens(self, text:str) -> int:
		'''Count the number of tokens in the passed text.'''
		return len(self.model.tokenize(text.encode("utf-8") if text != "" else [self.model.token_bos()], special=True))