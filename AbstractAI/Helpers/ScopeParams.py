from dataclasses import dataclass, field
from typing import Optional, Any, Dict, TypeVar, Type, List, Generic
import threading
from copy import deepcopy
from ClassyFlaskDB.DefaultModel import DATA, Object
from ClassyFlaskDB.new.ClassInfo import ClassInfo

T = TypeVar('T')
MISSING = object()

@DATA
@dataclass 
class ScopeParamsModel(Object):
	data_object: Optional[Any] = field(default=None)
	params: Dict[str, Any] = field(default_factory=dict)
	_all_params: Dict[str, Any] = field(default_factory=dict, init=False)
	
	def __post_init__(self):
		if self.data_object is None and ClassInfo.has_ClassInfo(type(self)):
			self.data_object = self
	
	@classmethod
	def create(cls, data_object: Optional[Any] = None, **kwargs):
		return ScopeParamsModel(data_object=data_object, params=kwargs)
			
	def _build_all_params(self, parent: Optional['ScopeParamsModel'] = None) -> Dict[str, Any]:
		"""
		Builds _all_params for this ScopeParams instance using parent's _all_params if available.
		Updates with data object fields and explicit params.
		"""
		all_params = parent._all_params.copy() if parent else {}
		
		# Add data object fields if present
		if self.data_object is not None:
			info = ClassInfo.get(self.data_object.__class__)
			if info:
				for field_name, field in info.fields.items():
					value = getattr(self.data_object, field_name)
					if value is not None:
						all_params[field_name] = value
		
		# Override with explicit params
		all_params.update(self.params)
		return all_params

	def __enter__(self):
		currentThread = threading.currentThread
		if not hasattr(currentThread, 'ScopeParams_stack'):
			currentThread.ScopeParams_stack = []
			
		parent = currentThread.ScopeParams_stack[-1] if currentThread.ScopeParams_stack else None
		self._all_params = self._build_all_params(parent)
		currentThread.ScopeParams_stack.append(self)
		return self

	def __exit__(self, exc_type, exc_val, exc_tb):
		currentThread = threading.currentThread
		currentThread.ScopeParams_stack.pop()
		if not currentThread.ScopeParams_stack:
			delattr(currentThread, 'ScopeParams_stack')

	@classmethod
	def get_param(cls, param_name: str, default: T = MISSING) -> T:
		currentThread = threading.currentThread
		if hasattr(currentThread, 'ScopeParams_stack') and currentThread.ScopeParams_stack:
			current = currentThread.ScopeParams_stack[-1]
			if param_name in current._all_params:
				return current._all_params[param_name]
		if default is not MISSING:
			return default
		raise KeyError(f"{param_name} not found in scope")

	@classmethod
	def get_object(cls, type_: Type[T]) -> Optional[T]:
		currentThread = threading.currentThread
		if hasattr(currentThread, 'ScopeParams_stack'):
			for params in reversed(currentThread.ScopeParams_stack):
				if params.data_object is not None and isinstance(params.data_object, type_):
					return params.data_object
		return None
	
	@classmethod
	def get_all_params(cls) -> Dict[str, Any]:
		currentThread = threading.currentThread
		if hasattr(currentThread, 'ScopeParams_stack') and currentThread.ScopeParams_stack:
			return currentThread.ScopeParams_stack[-1].all_params.copy()
		return {}

	@classmethod
	def get_stack(cls) -> 'ScopeParamsStack':
		currentThread = threading.currentThread
		return ScopeParamsStack(params=getattr(currentThread, 'ScopeParams_stack', []))
	
	@classmethod
	def get_nesting_level(cls) -> int:
		currentThread = threading.currentThread
		return len(getattr(currentThread, 'ScopeParams_stack', []))

class ScopeParams(ScopeParamsModel):
	def __init__(self, data_object: Optional[Any] = None, **kwargs) -> None:
		super().__init__(data_object, params=kwargs)

@DATA
@dataclass
class ScopeParamsStack(Object):
	params: List[ScopeParamsModel] = field(default_factory=list)

	# And in ScopeParamsStack:
	def __post_init__(self):
		# Rebuild all_params for each ScopeParams using previous as parent
		for i, param in enumerate(self.params):
			parent = self.params[i-1] if i > 0 else None
			param._all_params = param._build_all_params(parent)

	def make_current(self):
		currentThread = threading.currentThread
		currentThread.ScopeParams_stack = deepcopy(self.params)

if __name__ == "__main__":
	# Basic example:
	def my_method():
		param1 = ScopeParams.get_param('param1', default=0)
		param2 = ScopeParams.get_param('param2', default="")
		nesting_level = ScopeParams.get_nesting_level()
		all_params = ScopeParams.get_all_params()
		indent = "\t" * nesting_level
		print(f"{indent}param1: {param1}")
		print(f"{indent}param2: {param2}")
		print(f"{indent}Nesting Level: {nesting_level}")
		print(f"{indent}All Params: {all_params}")

	print(f"Outside any ScopeParams: Nesting Level: {ScopeParams.get_nesting_level()}")
	
	with ScopeParams(param1=5, param2=6):
		my_method()
		with ScopeParams(param1=42, param3="hello"):
			my_method()
		my_method()

	my_method()  # This will use default values
	
	# Example with dataclass's
	@DATA
	@dataclass
	class LLMParams(ScopeParamsModel):
		model: str = "gpt-3.5-turbo"
		temperature: float = 0.7
		max_tokens: Optional[int] = None

	@DATA
	@dataclass
	class BatchConfig:
		batch_size: int = 10
		parallel: bool = True
		timeout: float = 30.0

	print("\nStarting data class example...")
	nesting_level = ScopeParams.get_nesting_level()
	print(f"{'  ' * nesting_level}Initial nesting level: {nesting_level}")
	
	with LLMParams(temperature=0.9):
		indent = "  " * ScopeParams.get_nesting_level()
		print(f"{indent}Model: {ScopeParams.get_param('model')}")
		print(f"{indent}Temperature: {ScopeParams.get_param('temperature')}")
		
		batch_config = BatchConfig(batch_size=20)
		with ScopeParams(batch_config, temperature=0.5):
			indent = "  " * ScopeParams.get_nesting_level()
			print(f"{indent}Batch size: {ScopeParams.get_param('batch_size')}")
			print(f"{indent}Temperature: {ScopeParams.get_param('temperature')}")
			
			llm = ScopeParams.get_object(LLMParams)
			batch = ScopeParams.get_object(BatchConfig)
			print(f"{indent}Found LLMParams: {llm is not None}")
			print(f"{indent}Found BatchConfig: {batch is not None}")
			
			stack = ScopeParams.get_stack()
			print(f"{indent}Final stack depth: {len(stack.params)}")
			
			stack.make_current()
			print(f"{indent}After make_current - Temperature: {ScopeParams.get_param('temperature')}")