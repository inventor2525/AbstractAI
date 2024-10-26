import threading
from typing import TypeVar, Optional, Any, Dict

MISSING = object()

T = TypeVar('T')

class ScopeParams:
	_local = threading.local()

	def __init__(self, **kwargs):
		self.params = kwargs
		self.all_params: Dict[str, Any] = {}

	def __enter__(self):
		if not hasattr(ScopeParams._local, 'ScopeParams_stack'):
			ScopeParams._local.ScopeParams_stack = []
		if ScopeParams._local.ScopeParams_stack:
			parent = ScopeParams._local.ScopeParams_stack[-1]
			self.all_params = parent.all_params.copy()
		self.all_params.update(self.params)
		ScopeParams._local.ScopeParams_stack.append(self)
		return self

	def __exit__(self, exc_type, exc_val, exc_tb):
		ScopeParams._local.ScopeParams_stack.pop()
		if not ScopeParams._local.ScopeParams_stack:
			del ScopeParams._local.ScopeParams_stack

	@classmethod
	def get_param(cls, param_name: str, default: T = MISSING) -> T:
		if hasattr(cls._local, 'ScopeParams_stack') and cls._local.ScopeParams_stack:
			current = cls._local.ScopeParams_stack[-1]
			if param_name in current.all_params:
				return current.all_params[param_name]
		if default is not MISSING:
			return default
		raise KeyError(f"{param_name} not found in local scope. Use 'with ScopeParams(...)' to set it or pass a default to get.")

	@classmethod
	def get_all_params(cls) -> Dict[str, Any]:
		if hasattr(cls._local, 'ScopeParams_stack') and cls._local.ScopeParams_stack:
			return cls._local.ScopeParams_stack[-1].all_params.copy()
		return {}

	@classmethod
	def get_nesting_level(cls) -> int:
		return len(getattr(cls._local, 'ScopeParams_stack', []))

if __name__ == "__main__":
	# Example Usage
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