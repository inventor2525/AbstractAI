from dataclasses import dataclass, field
from ClassyFlaskDB.DefaultModel import *
from AbstractAI.Model.Converse.MessageSources.CallerInfo import CallerInfo
from typing import Callable, Dict, List, Optional, Union, Any, get_args, get_origin
from inspect import signature, getdoc, Parameter
from datetime import datetime

TOOL_MISSING = object()

@DATA(excluded_fields=["default"])
@dataclass
class ToolParameterInfo:
	name: str
	type: str
	description: str
	default: Any = TOOL_MISSING

@DATA(excluded_fields=["function"])
@dataclass
class Tool(Object):
	name: str
	description: str
	parameters: Dict[str, ToolParameterInfo]
	return_info: ToolParameterInfo
	function: Callable

	def __call__(self, *args: Any, **kwargs: Any) -> Any:
		return self.function(*args, **kwargs)

	@classmethod
	def from_function(
		cls,
		function: Callable,
		name: Union[str, object] = TOOL_MISSING,
		description: Union[str, object] = TOOL_MISSING,
		include_additional_description: Union[bool, List[str]] = False,
	) -> 'Tool':
		sig = signature(function)
		doc = getdoc(function)

		docstring_params = cls._parse_docstring(doc)

		if name is TOOL_MISSING:
			name = function.__name__

		if description is TOOL_MISSING:
			description = docstring_params.get('description', doc.split('\n\n')[0] if doc else "")

		parameters = {}

		for param_name, param in sig.parameters.items():
			param_info = ToolParameterInfo(
				name=param_name,
				type=cls._get_full_type_name(param.annotation),
				description=docstring_params.get(param_name, ""),
				default=param.default if param.default is not Parameter.empty else TOOL_MISSING
			)

			if include_additional_description:
				if isinstance(include_additional_description, list):
					if param_name in include_additional_description:
						param_info.description += cls._get_additional_description(param.annotation)
				else:
					param_info.description += cls._get_additional_description(param.annotation)

			parameters[param_name] = param_info

		return_info = None
		if sig.return_annotation is not Parameter.empty and sig.return_annotation is not None:
			return_info = ToolParameterInfo(
				name="return",
				type=cls._get_full_type_name(sig.return_annotation),
				description=docstring_params.get('return', ""),
			)
			if include_additional_description:
				if isinstance(include_additional_description, list):
					if "return" in include_additional_description:
						return_info.description += cls._get_additional_description(sig.return_annotation)
				else:
					return_info.description += cls._get_additional_description(sig.return_annotation)

		return cls(
			name=name,
			description=description,
			parameters=parameters,
			return_info=return_info,
			function=function,
		) | CallerInfo.catch([1])

	@staticmethod
	def _parse_docstring(docstring: Optional[str]) -> Dict[str, str]:
		if not docstring:
			return {}

		param_descriptions = {}
		lines = docstring.split('\n')
		current_param = None
		parsing_args = False
		general_description = []

		for line in lines:
			line = line.strip()
			if line.lower().startswith((':param', 'args:')):
				if general_description:
					param_descriptions['description'] = '\n'.join(general_description).strip()
					general_description = []
				
				if line.startswith(':param'):
					parts = line.split(':', 2)
					if len(parts) == 3:
						current_param = parts[1].split()[1]
						param_descriptions[current_param] = parts[2].strip()
				else:  # Args:
					parsing_args = True
					current_param = None
			elif line.startswith(':return:'):
				param_descriptions['return'] = line.split(':', 2)[2].strip()
			elif parsing_args and ':' in line:
				parts = line.split(':', 1)
				current_param = parts[0].strip()
				param_descriptions[current_param] = parts[1].strip()
			elif line.lower().startswith('returns:'):
				current_param = 'return'
				param_descriptions['return'] = line.split(':', 1)[1].strip()
			elif current_param and line:
				param_descriptions[current_param] += ' ' + line
			elif not parsing_args:
				general_description.append(line)

		if general_description:
			param_descriptions['description'] = '\n'.join(general_description).strip()

		return param_descriptions

	@staticmethod
	def _get_full_type_name(annotation: Any) -> str:
		if annotation is Parameter.empty:
			return "Any"
		
		def _get_name(ann):
			if hasattr(ann, "__name__"):
				return ann.__name__
			elif hasattr(ann, "_name"):
				return ann._name
			else:
				return str(ann).replace("typing.", "")

		origin = get_origin(annotation)
		if origin is None:
			return _get_name(annotation)
		
		args = get_args(annotation)
		arg_names = [Tool._get_full_type_name(arg) for arg in args]
		return f"{_get_name(origin)}[{', '.join(arg_names)}]"

	@staticmethod
	def _get_additional_description(annotation: Any) -> str:
		basic_types = {str, int, float, bool, list, dict, tuple, set, Any}

		def _get_leaf_types(ann):
			if get_origin(ann) is None:
				return [ann]
			return [leaf for arg in get_args(ann) for leaf in _get_leaf_types(arg)]

		leaf_types = _get_leaf_types(annotation)
		descriptions = []

		for leaf in leaf_types:
			if leaf not in basic_types and hasattr(leaf, "__doc__"):
				doc = leaf.__doc__
				if doc:
					descriptions.append(f" ({leaf.__name__}: {doc.split('.')[0]})")

		return "".join(descriptions)

if __name__ == "__main__":
	DATA.finalize()
	from typing import List, Dict, Optional
	from datetime import datetime, timedelta
	import ipaddress

	def get_weather(location: str, unit: str = "celsius") -> Dict[str, str]:
		"""
		Get the current weather for a given location.
		
		But in reality, it might do more than weather.
		
		Why?? Why would it do more than weather????
		
		Because we don't give a f* about the weather, all we want to know
		is if our doc string parser is working. :P

		:param location: The city and country, e.g., "London, UK"
		:param unit: The temperature unit, either "celsius" or "fahrenheit"
		:return: A dictionary containing weather information
		"""
		# Simulated weather data
		return {
			"location": location,
			"temperature": "22" if unit == "celsius" else "72",
			"unit": unit,
			"condition": "Partly cloudy"
		}

	def calculate_age(birth_date: datetime, current_date: Optional[datetime] = None) -> int:
		"""
		Calculate the age of a person based on their birth date.
		
		Parser working?

		Args:
			birth_date: The person's date of birth
			current_date: The date to calculate the age against (default is today)

		Returns:
			The calculated age in years
		"""
		if current_date is None:
			current_date = datetime.now()
		age = current_date.year - birth_date.year
		if current_date.month < birth_date.month or (current_date.month == birth_date.month and current_date.day < birth_date.day):
			age -= 1
		return age

	def process_data(data: List[Dict[str, Any]], filter_key: Optional[str] = None, ip_range: ipaddress.IPv4Network = ipaddress.IPv4Network("192.168.0.0/24")) -> Dict[str, Any]:
		"""
		Process a list of dictionaries and return summary statistics.

		:param data: A list of dictionaries containing the data to process
		:param filter_key: An optional key to filter the data by
		:param ip_range: An IPv4 network range to associate with the data
		:return: A dictionary containing summary statistics and network information
		"""
		if filter_key:
			filtered_data = [item for item in data if filter_key in item]
		else:
			filtered_data = data

		return {
			"count": len(filtered_data),
			"keys": list(set().union(*filtered_data)),
			"total_items": sum(len(item) for item in filtered_data),
			"network_address": str(ip_range.network_address),
			"broadcast_address": str(ip_range.broadcast_address),
			"num_addresses": ip_range.num_addresses
		}

	# Create Tool instances from the functions
	weather_tool = Tool.from_function(get_weather)
	age_tool = Tool.from_function(calculate_age, include_additional_description=["current_date"])
	process_tool = Tool.from_function(process_data, include_additional_description=True)

	# Print tool information
	for tool in [weather_tool, age_tool, process_tool]:
		print(f"Tool: {tool.name}")
		print(f"Description: {tool.description}")
		print("Parameters:")
		for param in tool.parameters.values():
			print(f"  {param.name}: {param.type}")
			print(f"    Description: {param.description}")
			if param.default is not TOOL_MISSING:
				print(f"    Default: {param.default}")
		if tool.return_info:
			print(f"Return: {tool.return_info.type}")
			print(f"  Description: {tool.return_info.description}")
		print()

	# Demonstrate tool usage
	print("Weather Tool Demo:")
	weather_result = weather_tool("New York, USA", unit="fahrenheit")
	print(f"Weather in New York: {weather_result}")
	print()

	print("Age Calculator Tool Demo:")
	birth_date = datetime(1990, 5, 15)
	age_result = age_tool(birth_date)
	print(f"Age of person born on {birth_date.date()}: {age_result}")
	print()

	print("Data Processing Tool Demo:")
	sample_data = [
		{"name": "Alice", "age": 30, "city": "New York"},
		{"name": "Bob", "age": 25, "country": "Canada"},
		{"name": "Charlie", "age": 35, "city": "London", "country": "UK"}
	]
	custom_ip_range = ipaddress.IPv4Network("10.0.0.0/16")
	processed_result = process_tool(sample_data, filter_key="city", ip_range=custom_ip_range)
	print(f"Processed data result: {processed_result}")