import inspect
from dataclasses import field, dataclass
from typing import Any, Callable, TypeVar

def function_to_model(func):
	argspec = inspect.getfullargspec(func)
	default_values = {}
	if argspec.defaults:
		for arg, default_value in zip(argspec.args[-len(argspec.defaults):], argspec.defaults):
			default_values[arg] = default_value
			
	namespace = {'__annotations__': {}}
	# usable_fields = dict(**{type(k):v for k,v in default_values.items()})
	# usable_fields.update(**argspec.annotations.items())
	for field_name, field_type in argspec.annotations.items():
		if field_name == 'return':
			continue
		namespace['__annotations__'][field_name] = field_type
		if field_name in default_values:
			default = default_values[field_name]
			default_type = type(default)
			if callable(default):
				default = lambda default=default: default
			elif default_type == list or default_type == dict or default_type == set or default_type == tuple:
				default = lambda default=default: default
		else:
			if field_type == int:
				default = 0
			elif field_type == float:
				default = 0.0
			elif field_type == str:
				default = ""
			elif field_type == bool:
				default = False
			elif field_type == list:
				default = list
			elif field_type == dict:
				default = dict
			elif field_type == set:
				default = set
			elif field_type == tuple:
				default = tuple
			elif field_type == Any:
				default = None
			else:
				default = None
		if callable(default):
			namespace[field_name] = field(default_factory=default, init=False)
		else:
			namespace[field_name] = field(default=default, init=False)
	return type(f"{func.__name__}__AutoSettingModel", (object,), namespace)

T = TypeVar('T')
def call_with_class(func:Callable[[Any], T], instance:Any) -> T:
    """
    Calls the given function with the attributes of a class instance as keyword arguments.
    
    Args:
        func: The function to be called with the dataclass instance's fields as keyword arguments.
        instance: A class instance whose fields are to be used as keyword arguments.
    
    Returns:
        The result of the function call.
    """
	
    # Extracting the function's parameter names
    func_params = inspect.signature(func).parameters
    
    # Building a dictionary of arguments that are both in the instance and the function's parameters
    kwargs = {param: getattr(instance, param) for param in func_params if hasattr(instance, param)}
    
    # Calling the function with the constructed keyword arguments
    return func(**kwargs)

if __name__ == "__main__":
	def test_func1(a:int, b:str, c:bool, d:list=[1,2,3], e:float=3.14, f:dict={"a":1,"b":2}) -> int:
		print("test_func1 ", a,b,c,d,e,f)
		return 42
	def test_func2(a,b,c:int,d,e,hello_str="hello",pi:float=3.14, sqrt2=1.4142) -> str:
		print("test_func2 ", a,b,c,d,e,hello_str,pi,sqrt2)
		return "Hello, World!"
	model1_stub = function_to_model(test_func1)
	model2_stub = function_to_model(test_func2)
	
	Model1 = dataclass(model1_stub)
	Model2 = dataclass(model2_stub)
	
	print("Model instances created with defaults from the function definitions:")
	print(Model1())
	print(Model2())
	print("\n")
	
	print("Function calls with those models passed as arguments:")
	return_val = call_with_class(test_func1, Model1())
	try:
		return_val = call_with_class(test_func2, Model2())
	except Exception as e:
		print("test_func2 can't be called, which is good cause our func to model only captures things with type hints or that have default values. test_func2 has neither for some of its arguments.")