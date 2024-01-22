from .LLM import *

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
import transformers

class HuggingFaceLLM(LLM):
	def __init__(self):
		super().__init__()
		self.model = None
		self.tokenizer = None
		self.del_token_type_ids=True
		self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
		self.other_parameters = {
			"tokenizer": {
				"use_fast": False,
				"trust_remote_code": True
			},
			"model": {
				"torch_dtype": torch.float16,
				"low_cpu_mem_usage": True,
				"device_map": "auto",
				"trust_remote_code": True
			}
		}
	
	def _load_model(self):
		self.tokenizer = AutoTokenizer.from_pretrained(self.model_name, **self.other_parameters["tokenizer"])
		self.model = AutoModelForCausalLM.from_pretrained(self.model_name, **self.other_parameters["model"])

	def start(self):
		super().start()
		
	def _raw_to_text(self, response) -> str:
		return self.tokenizer.decode(response, skip_special_tokens=True)
	
	def _raw_output_token_count(self, response) -> str:
		return len(response)
		
	def _serialize_raw_response(self, response:torch.Tensor) -> str:
		return json.dumps(response.tolist(), indent=4)
	
	def _prompt_str(self, prompt_string: str):
		inputs = self.tokenizer(prompt_string, return_tensors="pt")
		inputs_len = len(inputs['input_ids'][0])
		inputs = inputs.to(self.device)
		
		try:
			if self.del_token_type_ids:
				del inputs["token_type_ids"]
		except Exception as e:
			pass
		
		output_tokens = self.model.generate(**inputs, do_sample=True, top_p=0.95, top_k=0, max_new_tokens=1024)
		response_tokens = output_tokens[0][inputs_len:]
		
		return response_tokens