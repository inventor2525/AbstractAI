def merge_dictionaries(dictionary1:dict, dictionary2:dict):
	open_list = [(dictionary1, dictionary2)]
	
	while len(open_list) > 0:
		dict1, dict2 = open_list.pop()
		
		for key, value in dict2.items():
			if key not in dict1:
				dict1[key] = value
			else:
				if isinstance(value, dict):
					if isinstance(dict1[key], dict):
						open_list.append((dict1[key], value))
					else:
						dict1[key] = value
				else:
					dict1[key] = value
	return dictionary1

def replace_keys(dictionary:dict, replace_map:dict):
	dictionary = dictionary.copy()
	for key, value in dictionary.items():
		if key in replace_map:
			rm_value = replace_map[key]
			if isinstance(value, dict):
				dictionary[replace_map[key]] = replace_keys(value, rm_value)
			else:
				dictionary[rm_value] = value
			del dictionary[key]
	return dictionary

def replace_parameters(dictionary:dict, replace_map:dict):
	dictionary = dictionary.copy()
	for key, value in dictionary.items():
		if key in replace_map:
			rm_value = replace_map[key]
			if isinstance(value, dict):
				dictionary[key] = replace_parameters(value, rm_value)
			else:
				dictionary[key] = rm_value
	return dictionary