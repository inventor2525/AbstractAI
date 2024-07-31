from .LLMSettings import *

@DATA(id_type=ID_Type.HASHID)
@dataclass
class Groq_LLMSettings(LLMSettings):
	__ui_name__ = "Groq"
	model_name:str = ""
	
	api_key:str = ""
	base_url:str = ""
	
	def load(self):
		from AbstractAI.LLMs.Groq_LLM import Groq_LLM
		return Groq_LLM(self.copy())