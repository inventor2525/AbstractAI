from .LLM import LLM

from torch import bfloat16
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
import transformers

class HuggingFaceLLM(LLM):
	def __init__(self):
		super().__init__()
		self.model = None
		self.tokenizer = None
		self.del_token_type_ids=True
	
	def raw_to_text(self, response) -> str:
		return self.tokenizer.decode(response[0], skip_special_tokens=True)
	
	def raw_output_token_count(self, response) -> str:
		return len(response[0])
		
	def prompt(self, prompt: str):
		inputs = self.tokenizer(prompt, return_tensors="pt").to("cuda")
		try:
			if self.del_token_type_ids:
				del inputs["token_type_ids"]
		except Exception as e:
			pass
		output = self.model.generate(**inputs, do_sample=True, top_p=0.95, top_k=0, max_new_tokens=1024)
		return output