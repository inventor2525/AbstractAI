from .LLMSettings import *

@ConversationDATA(generated_id_type=ID_Type.HASHID)
class Ollama_LLMSettings(LLMSettings):
	__ui_name__ = "Ollama"
	model_name:str = ""
	def load(self):
		from AbstractAI.LLMs.Ollama_LLM import Ollama_LLM
		return Ollama_LLM(self.copy())