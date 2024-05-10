from .LLMSettings import *

@ConversationDATA
class OpenAI_LLMSettings(LLMSettings):
	api_key:str = ""
	base_url:str = ""
	organization: str = ""
	model_name:str = ""
	
	def load(self):
		from AbstractAI.LLMs.OpenAI_LLM import OpenAI_LLM
		# return OpenAI_LLM(self)