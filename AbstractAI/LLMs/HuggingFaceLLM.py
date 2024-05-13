from .LLM import *

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
import transformers

from AbstractAI.Settings.HuggingFace_LLMSettings import HuggingFace_LLMSettings

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
			trust_remote_code=self.settings.model.trust_remote_code
		)
	
	def _complete_str_into(self, prompt: str, wip_message:Message, stream:bool=False, max_tokens:int=None) -> LLM_Response:
		inputs = self.tokenizer(prompt, return_tensors="pt")
		inputs_len = len(inputs['input_ids'][0])
		inputs = inputs.to(self.device)
		
		response = LLM_Response(wip_message, inputs_len, stream)
		
		try:
			if self.settings.del_token_type_ids:
				del inputs["token_type_ids"]
		except Exception as e:
			pass
		
		if stream:
			# raise NotImplementedError("Stream not yet implemented for HuggingFaceLLM")
			pass
		else:
			replace_parameters = {}
			if max_tokens is not None:
				replace_parameters["max_new_tokens"] = max_tokens
			params = kwargs_from_instance(self.model.generate, self.settings.generate, replace_parameters)
			output_tokens = self.model.generate(**inputs, **params)
			response_tokens = output_tokens[0][inputs_len:]
			
			response_str = self.tokenizer.decode(response_tokens, skip_special_tokens=True)
			response.set_response(response_str, len(response_tokens), response_tokens.tolist())
		
		return response
	
	def _apply_chat_template(self, chat: List[Dict[str,str]], start_str:str="") -> str:
		chat_str = self.tokenizer.apply_chat_template(chat, tokenize=False, add_generation_prompt=True)
		if start_str is not None and len(start_str) > 0:
			chat_str = chat_str + start_str
		return chat_str
	
	def count_tokens(self, text:str) -> int:
		'''Count the number of tokens in the passed text.'''
		return len(self.tokenizer(text)["input_ids"][0])