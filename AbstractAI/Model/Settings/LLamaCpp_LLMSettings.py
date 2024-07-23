from .LLMSettings import *

@DATA(id_type=ID_Type.HASHID)
@dataclass
class LLamaCpp_LLMInitSettings(Object):
	'''
	Used to load the model.
	'''
	model_path:str = ""
	n_ctx:int = 2048
	
	n_gpu_layers:int = 0
	n_threads:int = 1
	
	main_gpu:int = 0
	
	chat_format:str = None
	flash_attn:bool = False
	verbose:bool = False

@DATA(id_type=ID_Type.HASHID)
@dataclass
class LLamaCpp_LLMGenerateSettings(Object):
	'''
	Used when generating text with the model.
	'''
	temperature: float = 0.8
	top_p: float = 0.95
	min_p: float = 0.05
	typical_p: float = 1.0
	echo: bool = False
	frequency_penalty: float = 0.0
	presence_penalty: float = 0.0
	repeat_penalty: float = 1.1
	top_k: int = 40
	tfs_z: float = 1.0
	mirostat_mode: int = 0
	mirostat_tau: float = 5.0
	mirostat_eta: float = 0.1
	
@DATA(id_type=ID_Type.HASHID)
@dataclass
class LLamaCpp_LLMSettings(LLMSettings):
	__ui_name__ = "LLamaCPP"
	model:LLamaCpp_LLMInitSettings = field(default_factory=LLamaCpp_LLMInitSettings)
	generate:LLamaCpp_LLMGenerateSettings = field(default_factory=LLamaCpp_LLMGenerateSettings)
	
	def load(self):
		from AbstractAI.LLMs.LLamaCPP_LLM import LLamaCPP_LLM
		return LLamaCPP_LLM(self.copy())