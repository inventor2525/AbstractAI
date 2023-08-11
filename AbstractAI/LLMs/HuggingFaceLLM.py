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
	
	def raw_to_text(self, response) -> str:
		return self.tokenizer.decode(response, skip_special_tokens=True)
	
	def raw_output_token_count(self, response) -> str:
		return len(response)
		
	def prompt(self, prompt: str):
		inputs = self.tokenizer(prompt, return_tensors="pt")
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