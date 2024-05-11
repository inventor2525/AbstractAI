from AbstractAI.LLMs.OpenAI_LLM import *
from groq import Groq

class Groq_LLM(OpenAI_LLM):
	def _load_model(self):
		self.client = Groq(api_key=self.settings.api_key)
	
	def count_tokens(self, text:str, model_name:str=None) -> int:
		return -1