from .LLM import *

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
import transformers

from AbstractAI.Model.Settings.HuggingFace_LLMSettings import HuggingFace_LLMSettings

class HuggingFaceLLM(LLM):
	def __init__(self, settings:HuggingFace_LLMSettings):
		self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu') if settings.model.device_map == "auto" else settings.model.device
		super().__init__(settings)
		self.model = None
		self.tokenizer = None
	
	def _load_model(self):
		# more_model_params = {"torch_dtype": torch.float16}
		
		# bnb_config = None
		# bnb_config_dict = self.model_info.parameters.get("bnb_config", None)
		# if bnb_config_dict is not None:
		# 	bnb_config = transformers.BitsAndBytesConfig(**bnb_config_dict)
		# 	more_model_params["quantization_config"] = bnb_config
		
		self.tokenizer = AutoTokenizer.from_pretrained(
			self.settings.model_str, 
			use_fast=self.settings.tokenize.use_fast, 
			trust_remote_code=self.settings.tokenize.trust_remote_code
		)
		self.model = AutoModelForCausalLM.from_pretrained(
			self.settings.model_str,
			# revision=self.settings.model.revision,
			torch_dtype=self.settings.model.torch_dtype.to_torch(),
			low_cpu_mem_usage=self.settings.model.low_cpu_mem_usage,
			device_map=self.settings.model.device_map,
			# device=self.device,
			trust_remote_code=self.settings.model.trust_remote_code,
			attn_implementation='eager'
		)
	
	def chat(self, conversation: Conversation, start_str:str="", stream=False, max_tokens:int=None) -> Union[LLM_Response, Iterator[LLM_Response]]:
		wip_message, message_list = self._new_message(conversation, start_str)
		
		replace_parameters = {}
		if max_tokens is not None:
			replace_parameters["max_new_tokens"] = max_tokens
		params = kwargs_from_instance(self.model.generate, self.settings.generate, replace_parameters)
	
		inputs_local = self.tokenizer(wip_message.source.prompt, return_tensors="pt")
		wip_message.source.in_token_count = len(inputs_local['input_ids'][0])
		inputs = inputs_local.to(self.device)
		
		try:
			if self.settings.del_token_type_ids:
				del inputs["token_type_ids"]
		except:
			pass
	
		response = LLM_Response(wip_message, stop_streaming_func=None)
		if stream:
			#stream not supported in this HF implementation, but we need to be an iterator so...
			yield response 
			
		output_tokens = self.model.generate(**inputs, **params)
		response_tokens = output_tokens[0][response.source.in_token_count:]
		
		response.source.finished = True
		response.message.content = self.tokenizer.decode(response_tokens, skip_special_tokens=True)
		response.source.out_token_count = len(response_tokens)
		response.source.serialized_raw_output = {
			"in_tokens":inputs_local['input_ids'][0].tolist(),
			"out_tokens":response_tokens.tolist()
		}
		response.source.generating = False
		wip_message.emit_changed()
		return response
	
	def _apply_chat_template(self, chat: List[Dict[str,str]], start_str:str="") -> str:
		chat_str = self.tokenizer.apply_chat_template(chat, tokenize=False, add_generation_prompt=True)
		if start_str is not None and len(start_str) > 0:
			chat_str = chat_str + start_str
		return chat_str
	
	def count_tokens(self, text:str) -> int:
		'''Count the number of tokens in the passed text.'''
		return len(self.tokenizer(text)["input_ids"][0])