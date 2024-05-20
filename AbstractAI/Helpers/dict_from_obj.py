def dict_from_obj(obj):
	"""
	Recursively convert an object and all nested objects to dictionaries.
	"""
	if isinstance(obj, dict):
		return {k: dict_from_obj(v) for k, v in obj.items()}
	elif isinstance(obj, (list, tuple, set)):
		return [dict_from_obj(item) for item in obj]
	elif not isinstance(obj, (str, int, float, bool)) and hasattr(obj, "__dict__"):
		return {k: dict_from_obj(v) for k, v in obj.__dict__.items()}
	else:
		return obj