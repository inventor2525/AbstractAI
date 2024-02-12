from .LLM import *

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
import transformers

class HuggingFaceLLM(LLM):
	def __init__(self, model_name:str, parameters:Dict[str, Any]={}):
		default = {
			"tokenizer": {
				"use_fast": False,
				"trust_remote_code": True
			},
			"model": {
				"torch_dtype": torch.float16,
				"low_cpu_mem_usage": True,
				"device_map": "auto",
				"trust_remote_code": True
			},
			"generate": {
				"do_sample":True,
				"top_p":0.95,
				"top_k":0,
				"max_new_tokens":1024
			},
			"bnb_config" : {
				"load_in_4bit":True,
				"bnb_4bit_quant_type":'nf4',
				"bnb_4bit_use_double_quant":True,
				"bnb_4bit_compute_dtype":torch.bfloat16
			},
			"del_token_type_ids": True
		}
		
		self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu') if parameters["model"]["device_map"] == "auto" else parameters["model"].get("device", 'cpu')
		
		super().__init__(model_name, merge_dictionaries(default, parameters))
		self.model = None
		self.tokenizer = None
	
	def _load_model(self):
		bnb_config = None
		bnb_config_dict = self.model_info.parameters.get("bnb_config", None)
		if bnb_config_dict is not None:
			bnb_config = transformers.BitsAndBytesConfig(**bnb_config_dict)
		self.tokenizer = AutoTokenizer.from_pretrained(self.model_name, **self.model_info.parameters["tokenizer"])
		self.model = AutoModelForCausalLM.from_pretrained(self.model_name, quantization_config=bnb_config, **self.model_info.parameters["model"])

	def _complete_str_into(self, prompt: str, wip_message:Message, stream:bool=False) -> LLM_Response:
		inputs = self.tokenizer(prompt, return_tensors="pt")
		inputs_len = len(inputs['input_ids'][0])
		inputs = inputs.to(self.device)
		
		response = LLM_Response(wip_message, inputs_len, stream)
		
		try:
			if self.model_info.parameters["del_token_type_ids"]:
				del inputs["token_type_ids"]
		except Exception as e:
			pass
		
		if stream:
			raise NotImplementedError("Stream not yet implemented for HuggingFaceLLM")
		else:
			output_tokens = self.model.generate(**inputs, **self.model_info.parameters["generate"])
			response_tokens = output_tokens[0][inputs_len:]
			
			response_str = self.tokenizer.decode(response_tokens, skip_special_tokens=True)
			response.set_response(response_str, len(response_tokens), response_tokens.tolist())
		
		return response
	
	def _apply_chat_template(self, chat: List[Dict[str,str]], start_str:str="") -> str:
		chat_str = self.tokenizer.apply_chat_template(chat, tokenize=False, add_generation_prompt=True)
		if start_str is not None and len(start_str) > 0:
			chat_str = chat_str + start_str
		return chat_str