from .LLMSettings import *

@ConversationDATA
class Groq_LLMSettings(LLMSettings):
	'''
	Used to load the model.
	'''
	api_key:str = ""
	base_url:str = ""
	model_name:str = ""
	
	def load(self):
		from AbstractAI.LLMs.Groq_LLM import Groq_LLM
		# return Groq_LLM(self)