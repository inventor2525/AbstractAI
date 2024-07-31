from ClassyFlaskDB.DefaultModel import *
from dataclasses import field
from copy import deepcopy
from typing import List
from typing import Dict

@DATA
@dataclass
class Hacky_Whisper_Settings(Object):
	groq_api_key:str = None
	use_groq:bool = True
	
	#local (non-groq) use only:
	model_name:str="small.en"
	device:str="cpu"
	compute_type:str="int8"