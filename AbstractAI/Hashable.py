import hashlib
from functools import wraps
from typing import get_type_hints
from itertools import chain

class HashableProperty(property):
	def __init__(self, fget=None, fset=None, fdel=None, doc=None):
		super().__init__(fget, fset, fdel, doc)
		self.is_hashable = True

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
	type_hint = get_type_hints(func).get('value', object)

	def getter(self):
		return getattr(self, property_name, None)

	def setter(self, value):
		if value is not None and not isinstance(value, type_hint):
			raise TypeError(f"Expected type {type_hint}, got {type(value)}")
		setattr(self, property_name, value)
		self._hash = None

	return HashableProperty(getter, setter).setter(setter)

if __name__ == "__main__":
	class Child(Hashable):
		def __init__(self):
			super().__init__()

		@hash_property
		def value_0(self, value: int):
			'''This is the value_0 property.'''
			pass

	# Create an instance of the Child class
	child = Child(42)

	# Access and print the value_0 property
	print("Initial value_0:", child.value_0)

	# Print the initial hash
	print("Initial hash:", child.hash)

	# Set the value_0 property
	child.value_0 = 100

	# Access and print the updated value_0 property
	print("Updated value_0:", child.value_0)

	# Print the updated hash
	print("Updated hash:", child.hash)
