from AbstractAI.LLMs.CommonRoles import CommonRoles
from .LLM import *

from llama_cpp import Llama
from llama_cpp.llama_chat_format import LlamaChatCompletionHandlerRegistry, ChatFormatter, ChatFormatterResponse
from AbstractAI.Model.Settings.LLamaCpp_LLMSettings import LLamaCpp_LLMSettings

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
	
	def chat(self, conversation: Conversation, start_str:str="", stream=False, max_tokens:int=None, auto_append:bool=False) -> Union[LLM_Response, Iterator[LLM_Response]]:
		wip_message, message_list = self._new_message(conversation, start_str, auto_append=auto_append)
		
		params = kwargs_from_instance(self.model.create_completion, self.settings.generate)
		
		if max_tokens is not None:
			params["max_tokens"] = max_tokens
		
		completion = self.model(
			wip_message.source.prompt,
			**params,
			stream=stream
		)
		
		if stream:
			response = LLM_Response(wip_message, completion.close)
			response.message.content = start_str
			yield response
			
			for i, chunk in enumerate(completion):
				if response.message.append(chunk['choices'][0]['text']):
					response.source.out_token_count += 1
				response.log_chunk(chunk)
				response.source.finished = chunk['choices'][0].get('finish_reason', None) == 'stop'
				yield response
			response.source.generating = False
		else:
			response.source.finished = completion['choices'][0]['finish_reason'] == 'stop'
			response.message.append(completion['choices'][0]['text'])
			response.source.in_token_count = completion["usage"]["prompt_tokens"]
			response.source.out_token_count = completion["usage"]["completion_tokens"]
			response.source.serialized_raw_output = completion
			response.source.generating = False
		
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