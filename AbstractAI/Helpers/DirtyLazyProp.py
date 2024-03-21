def lazy_property(func):
	'''
	A decorator to make a property lazy-evaluated.
	
	Simply add this decorator to a property getter method and return
	a slow-to-calculate value. The first time the property is accessed,
	the value will be calculated and stored in a private attribute with
	the same name as the property, but with a leading underscore. The
	value will then be returned from the private attribute on subsequent
	accesses.
	
	When the object is marked as dirty, the property will be recalculated
	the next time it is accessed. This is done by setting a dirty attribute
	with the same name as the property, but with a leading underscore and
	a trailing '_dirty'. This attribute will be set to True, and the
	private attribute will be recalculated the next time the property is
	accessed.
	
	To mark the object as dirty, call the _dirty() method on the object.
	
	The _dirty() method is added to the class by the dirtyable class decorator.
	'''
	attr_name = '_' + func.__name__
	dirty_attr_name = '_' + func.__name__ + '_dirty'
	
	@property
	def _lazy_prop(self):
		if not hasattr(self, attr_name) or getattr(self, dirty_attr_name, True):
			setattr(self, attr_name, func(self))
			setattr(self, dirty_attr_name, False)
		
		# store the dirty_attr_name in a list of dirty attributes for the class:
		if not hasattr(self, '_dirty_attributes'):
			setattr(self, '_dirty_attributes', set())
		self._dirty_attributes.append(dirty_attr_name)
		
		setattr(self, '_completely_dirty', False)
		return getattr(self, attr_name)
	return _lazy_prop

def dirtyable(cls):
	'''
	A class decorator to add a _dirty() method to a class.
	
	When the _dirty() method is called, it marks the object as dirty,
	causing all lazy properties to be recalculated the next time they
	are accessed.
	
	It is safe to call _dirty() multiple times, as it will only mark
	all lazy properties as dirty when called the first time after
	any of the lazy properties have been accessed.
	'''
	def _dirty(self):
		if getattr(self, '_completely_dirty', True):
			return
		for attr_name in getattr(self, '_dirty_attributes', []):
			setattr(self, attr_name, True)
		setattr(self, '_completely_dirty', True)
	setattr(cls, '_dirty', _dirty)
	return cls