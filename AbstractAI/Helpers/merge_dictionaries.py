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