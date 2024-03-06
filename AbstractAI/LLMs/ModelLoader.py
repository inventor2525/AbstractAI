from AbstractAI.LLMs.LLM import LLM
from AbstractAI.Helpers.merge_dictionaries import merge_dictionaries

import json
from typing import Dict, Any
from enum import Enum
import pkgutil
import os

class ModelType(Enum):
	HuggingFace = "HuggingFace"
	LLamaCPP = "LLamaCPP"
	OpenAI = "OpenAI"
	RemoteLLM = "RemoteLLM"
	GroqLLM = "GroqLLM"

class ModelLoader():
	def __init__(self, model_configs:Dict[str, Any]={}):
		# Load package model configs
		package_directory = os.path.dirname(os.path.abspath(pkgutil.get_loader('AbstractAI').path))
		model_configs_path = os.path.join(package_directory, 'models.json')
		if os.path.exists(model_configs_path):
			with open(model_configs_path, 'r') as f:
				package_model_configs = json.load(f)
				model_configs = merge_dictionaries(model_configs, package_model_configs)
		
		# Load user model configs (~/.config/AbstractAI/models.json)
		user_model_configs_path = os.path.join(os.path.expanduser("~"), '.config', 'AbstractAI', 'models.json')
		if os.path.exists(user_model_configs_path):
			with open(user_model_configs_path, 'r') as f:
				user_model_configs = json.load(f)
				model_configs = merge_dictionaries(model_configs, user_model_configs)
		
		self.model_configs = model_configs
	
	@property
	def model_names(self):
		return self.model_configs.keys()
	
	def __getitem__(self, model_name:str) -> LLM:
		config = self.model_configs.get(model_name, None)
		if config is None:
			raise KeyError(f"Model '{model_name}' not found in model configs.")
		
		model_name = config.get("ModelName", model_name)
		
		loader_type = config.get("LoaderType", None)
		if loader_type is None:
			raise KeyError(f"Model '{model_name}' does not have a LoaderType.")
		
		llm = None
		if loader_type == ModelType.HuggingFace.value:
			from AbstractAI.LLMs.HuggingFaceLLM import HuggingFaceLLM
			llm = HuggingFaceLLM(model_name, config.get("Parameters", {}))
		
		elif loader_type == ModelType.LLamaCPP.value:
			model_path = config.get("ModelPath", None)
			if model_path is None:
				raise KeyError(f"Model '{model_name}' does not have a ModelPath.")
			
			from AbstractAI.LLMs.LLamaCPP_LLM import LLamaCPP_LLM
			llm = LLamaCPP_LLM(model_name, model_path, config.get("Parameters", {}))
		
		elif loader_type == ModelType.OpenAI.value:
			assert "APIKey" in config, f"Model '{model_name}' does not have an APIKey."
			api_key = config["APIKey"]
			
			from AbstractAI.LLMs.OpenAI_LLM import OpenAI_LLM
			llm = OpenAI_LLM(api_key, model_name, config.get("Parameters", {}))
		
		elif loader_type == ModelType.RemoteLLM.value:
			from AbstractAI.LLMs.RemoteLLM import RemoteLLM
			llm = RemoteLLM(model_name, config.get("Parameters", {}))
		
		elif loader_type == ModelType.GroqLLM.value:
			assert "APIKey" in config, f"Model '{model_name}' does not have an APIKey."
			api_key = config["APIKey"]
			
			from AbstractAI.LLMs.Groq_LLM import Groq_LLM
			llm = Groq_LLM(api_key, model_name, config.get("Parameters", {}))
			
		if llm is not None:
			llm.model_info.config = config
		
		return llm
		
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