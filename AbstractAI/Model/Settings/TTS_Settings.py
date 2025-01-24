from ClassyFlaskDB.DefaultModel import *

@DATA
@dataclass
class TTS_Settings_v1(Object):
	use_groq:bool = True
	groq_api_key:str = None
	groq_model_name:str = "whisper-large-v3"
	
	enable_local_fallback:bool = True
	local_model_name:str = "small.en"
	local_device:str = "cpu"
	local_compute_type:str = "int8"