from .LLMSettings import *
from enum import Enum

class torch_dtype_redefine(Enum):
	int = "int"
	int8 = "int8"
	int16 = "int16"
	int32 = "int32"
	int64 = "int64"
	float = "float"
	float16 = "float16"
	float32 = "float32"
	float64 = "float64"
	double = "double"
	bool = "bool"
	
	uint8 = "uint8"
	half = "half"
	short = "short"
	long = "long"
	
	bfloat16 = "bfloat16"
	complex32 = "complex32"
	complex64 = "complex64"
	cfloat = "cfloat"
	complex128 = "complex128"
	cdouble = "cdouble"
	quint8 = "quint8"
	qint8 = "qint8"
	qint32 = "qint32"
	quint4x2 = "quint4x2"
	quint2x4 = "quint2x4"
	
	def to_torch(self) -> "torch.dtype":
		try:
			import torch
			return getattr(torch, self.value)
		except Exception as e:
			raise e
	
@DATA(generated_id_type=ID_Type.HASHID)
@dataclass
class HuggingFace_LLMInitSettings:
	'''
	Used to load the model.
	'''
	revision:str = ""
	torch_dtype:torch_dtype_redefine = torch_dtype_redefine.float16
	low_cpu_mem_usage:bool = True
	device_map:str = "auto"
	device:str = None
	trust_remote_code:bool = False

@DATA(generated_id_type=ID_Type.HASHID)
@dataclass
class HuggingFace_LLMGenerateSettings:
	'''
	Used when generating text with the model.
	'''
	do_sample:bool = False
	top_p:float = 0.95
	top_k:int = 0

@DATA(generated_id_type=ID_Type.HASHID)
@dataclass
class HuggingFace_LLMTokenizerSettings:
	'''
	Used to load the tokenizer.
	'''
	use_fast:bool = False
	trust_remote_code:bool = False
# "bnb_config" : {
			# 	"load_in_4bit":True,
			# 	"bnb_4bit_quant_type":'nf4',
			# 	"bnb_4bit_use_double_quant":True,
			# 	"bnb_4bit_compute_dtype":torch.bfloat16
			# },
@DATA(generated_id_type=ID_Type.HASHID)
@dataclass
class HuggingFace_LLMSettings(LLMSettings):
	__ui_name__ = "HuggingFace"
	model_str:str = ""
	del_token_type_ids:bool = True
	model :HuggingFace_LLMInitSettings = field(default_factory=HuggingFace_LLMInitSettings)
	generate :HuggingFace_LLMGenerateSettings = field(default_factory=HuggingFace_LLMGenerateSettings)
	tokenize :HuggingFace_LLMTokenizerSettings = field(default_factory=HuggingFace_LLMTokenizerSettings)
	
	def load(self):
		from AbstractAI.LLMs.HuggingFaceLLM import HuggingFaceLLM
		return HuggingFaceLLM(self.copy())