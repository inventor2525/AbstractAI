from ClassyFlaskDB.DefaultModel import *

@DATA
@dataclass
class EditSource(Object):
	"""A message source representing an edited message."""
	original: Object
	new: Object = None
	
	def original_object(self) -> Object:
		"""
		Returns the most original object in the edit chain.
		"""
		prev = self.original
		while prev is not None and prev.source is not None:
			if isinstance(prev.source, EditSource):
				prev = prev.source.original
			else:
				break
			
		return prev
	
	def original_source(self) -> Object:
		"""
		Returns the most original object source in the edit chain.
		"""
		return self.original_object().source