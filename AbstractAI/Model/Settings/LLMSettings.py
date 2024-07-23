from ClassyFlaskDB.DefaultModel import *
from dataclasses import field
from copy import deepcopy
from typing import List
from typing import Dict

@DATA(id_type=ID_Type.HASHID)
@dataclass
class RolesSettings(Object):
	accepts_system_messages:bool = True
	must_alternate:bool = False
	merge_consecutive_messages_by_same_role:bool = True
	
	System:str = "system"
	User:str = "user"
	Assistant:str = "assistant"

@DATA(id_type=ID_Type.HASHID)
@dataclass
class LLMSettings(Object):
	user_model_name:str = field(default="", kw_only=True)
	user_description:str = field(default="", kw_only=True)
	roles:RolesSettings = field(default_factory=RolesSettings, kw_only=True)
	
	def load(self) -> "LLM":
		raise NotImplementedError("Subclasses must implement this method.")
	
	@classmethod
	def ui_name(cls) -> str:
		if hasattr(cls, "__ui_name__"):
			return cls.__ui_name__
		return cls.__name__.replace("_", " ")
	
	@staticmethod
	def load_subclasses() -> Dict[str,"LLMSettings"]:
		'''
		Load all subclasses of this class from the same directory.
		
		Returns a dictionary with the UI names of the subclasses as
		keys and the subclassed types as values.
		'''
		import importlib
		import inspect
		import os

		# Get a list of all Python files in the directory of this class
		files = []
		for root, dirs, filenames in os.walk(os.path.dirname(__file__)):
			for filename in filenames:
				if filename.endswith('.py'):
					files.append(filename[:-3])  # Remove .py extension

		classes = {}
		for file in files:
			module_name = '.' + file
			module = importlib.import_module(module_name, package=__package__)
			for name, obj in inspect.getmembers(module, inspect.isclass):
				if issubclass(obj, LLMSettings) and obj != LLMSettings:
					classes[obj.ui_name()] = obj

		return classes
	
	def copy(self) -> "LLMSettings":
		'''
		Returns a deep copy of this object with a new ID.
		'''
		copy = deepcopy(self)
		copy.new_id(True)
		copy._copy_source_ = self
		return copy

@DATA
@dataclass
class LLMConfigs(Object):
	models:List[LLMSettings] = field(default_factory=list)