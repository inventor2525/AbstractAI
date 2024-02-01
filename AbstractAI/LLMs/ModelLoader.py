from AbstractAI.LLMs.LLM import LLM

import json
from typing import Dict, Any
from enum import Enum

class ModelType(Enum):
	HuggingFace = "HuggingFace"
	LLamaCPP = "LLamaCPP"
	OpenAI = "OpenAI"

class ModelLoader():
	def __init__(self, model_configs:Dict[str, Any]={}):
		self.model_configs = model_configs
	
	@property
	def model_names(self):
		return self.model_configs.keys()
	
	def __getitem__(self, model_name:str) -> LLM:
		config = self.model_configs.get(model_name, None)
		if config is None:
			raise KeyError(f"Model '{model_name}' not found in model configs.")
		
		loader_type = config.get("LoaderType", None)
		if loader_type is None:
			raise KeyError(f"Model '{model_name}' does not have a LoaderType.")
		
		if loader_type == ModelType.HuggingFace.value:
			from AbstractAI.LLMs.HuggingFaceLLM import HuggingFaceLLM
			return HuggingFaceLLM(model_name, config.get("Parameters", {}))
		
		if loader_type == ModelType.LLamaCPP.value:
			model_path = config.get("ModelPath", None)
			if model_path is None:
				raise KeyError(f"Model '{model_name}' does not have a ModelPath.")
			
			from AbstractAI.LLMs.LLamaCPP_LLM import LLamaCPP_LLM
			return LLamaCPP_LLM(model_name, model_path, config.get("Parameters", {}))
		
		# if loader_type == ModelType.OpenAI.value:
		#	from AbstractAI.LLMs.OpenAI_LLM import OpenAI_LLM
		# 	return OpenAI_LLM(model_name, config.get("Parameters", {}))
		
	def add_config(self, model_name:str, loader_type:ModelType, model_path:str=None, parameters:Dict[str, Any]={}):
		if loader_type == ModelType.LLamaCPP:
			if model_path is None:
				raise KeyError(f"Model '{model_name}' does not have a ModelPath.")
		
		if model_path is not None:
			self.model_configs[model_name] = {
				"LoaderType": loader_type.value,
				"ModelPath": model_path,
				"Parameters": parameters
			}
		else:
			self.model_configs[model_name] = {
				"LoaderType": loader_type.value,
				"Parameters": parameters
			}