from .LLMSettings import *

@DATA(id_type=ID_Type.HASHID)
@dataclass
class OpenAI_LLMSettings(LLMSettings):
	__ui_name__ = "OpenAI"
	model_name:str = ""
	
	api_key:str = ""
	base_url:str = ""
	organization: str = ""
	
	temperature: float = 0.2
	def load(self):
		from AbstractAI.LLMs.OpenAI_LLM import OpenAI_LLM
		return OpenAI_LLM(self.copy())