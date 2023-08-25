import hashlib
from functools import wraps
from typing import get_type_hints
from itertools import chain

class Hashable:
	def __init__(self):
		self._hash = None
		self._hash_properties = [
			name for name in dir(self) 
			if isinstance(getattr(self.__class__, name, None), property) 
			and getattr(getattr(self.__class__, name, None), 'is_hashable', False)
		]
		self._additional_hash_fields = []
	
	def add_hash_field(self, field_name: str):
		'''Adds a field/property not decorated with hash_property'''
		self._additional_hash_fields.append(field_name)
		
	def recompute_hash(self):
		hash_items = (
			getattr(self, name, None) for name in 
			chain(self._hash_properties, self._additional_hash_fields)
		)
		self._hash = self._compute_hash(tuple(hash_items))

	def _compute_hash(self, x: object) -> str:
		return hashlib.sha256(str(x).encode("utf-8")).hexdigest()

	@property
	def hash(self) -> str:
		if self._hash is None:
			self.recompute_hash()
		return self._hash

def hash_property(func):
	property_name = f"_{func.__name__}"
	type_hint = get_type_hints(func).get('value', object)  # Default to object if no type hint

	@property
	@wraps(func)
	def getter(self):
		return getattr(self, property_name, None)  # Return None if backing field does not exist

	@getter.setter
	def setter(self, value):
		if not isinstance(value, type_hint):
			raise TypeError(f"Expected type {type_hint}, got {type(value)}")
		setattr(self, property_name, value)
		self._hash = None

	getter.is_hashable = True
	return getter