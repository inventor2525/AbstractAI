from ClassyFlaskDB.DefaultModel import *

@DATA
@dataclass
class Hacky_Whisper_Settings(Object):
	groq_api_key:str = None
	use_groq:bool = True
	
	#local (non-groq) use only:
	model_name:str="small.en"
	device:str="cpu"
	compute_type:str="int8"