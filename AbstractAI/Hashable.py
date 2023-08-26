import hashlib
from functools import wraps
from typing import get_type_hints
from itertools import chain

class HashableProperty(property):
	def __init__(self, fget=None, fset=None, fdel=None, doc=None):
		super().__init__(fget, fset, fdel, doc)
		self.is_hashable = True

class Hashable():
	def __init__(self):
		self._hash = None
		self._hash_properties = [
			name for name in dir(self) 
			if isinstance(getattr(self.__class__, name, None), property) 
			and getattr(getattr(self.__class__, name, None), 'is_hashable', False)
		]
		self._additional_hash_fields = []
		
		# Callbacks that notify that the hash has been spoiled.
		self.hash_spoiled = set([])
	
	def add_hash_field(self, field_name: str):
		self._additional_hash_fields.append(field_name)
		
	def recompute_hash(self):
		hash_items = (
			getattr(self, name, None).hash if isinstance(getattr(self, name, None), Hashable) else getattr(self, name, None) 
			for name in chain(self._hash_properties, self._additional_hash_fields)
		)
		self._hash = self._compute_hash(tuple(hash_items))

	def _compute_hash(self, x: object) -> str:
		return hashlib.sha256(str(x).encode("utf-8")).hexdigest()

	@property
	def hash(self) -> str:
		if self._hash is None:
			self.recompute_hash()
		return self._hash
	
	def spoil_hash(self):
		'''Marks the hash as needing to be re-calculated'''
		self._hash = None
		to_remove = []
		for callback in self.hash_spoiled:
			try:
				callback()
			except:
				to_remove.append(callback)
		for r in to_remove:
			self.hash_spoiled.remove(r)

def hash_property(func):
	property_name = f"_{func.__name__}"
	type_hint = [None]  # Use a mutable default to store the evaluated type hint

	def getter(self):
		return getattr(self, property_name, None)

	def setter(self, value):
		if type_hint[0] is None:
			try:
				type_hint_str = func.__annotations__.get('value', 'object')
				if isinstance(type_hint_str, str):
					type_hint[0] = eval(type_hint_str, globals(), self.__class__.__dict__)
				else:
					type_hint[0] = type_hint_str
			except NameError:
				pass  # Defer type checking until type can be resolved
		if type_hint[0] is not None and value is not None and not isinstance(value, type_hint[0]):
			raise TypeError(f"Expected type {type_hint[0]}, got {type(value)}")
		func(self, value)  # Call the original setter function
		setattr(self, property_name, value)
		self.spoil_hash()

	return HashableProperty(getter, setter).setter(setter)

if __name__ == "__main__":
	class Child(Hashable):
		def __init__(self, value1: int):
			super().__init__()
			self.value_0 = value1
			self.some_field = "additional data"
			self.add_hash_field('some_field')

		@hash_property
		def value_0(self, value: int):
			'''This is the value_0 property.'''
			print("Additional stuff that can happen before the setter logic happens inside hash_property")

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
	
	
	# Change some_field
	child.some_field = "Other val"
	
	# Observe that the has was not auto updated:
	print("Updated hash:", child.hash)

	# Manually Recompute the hash for things that don't use the hash_property
	child.recompute_hash()

	# Print the updated hash
	print("Updated hash:", child.hash)
