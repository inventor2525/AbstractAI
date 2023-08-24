import hashlib

class Hashable():
	def __init__(self):
		self._hash = None
	
	def recompute_hash(self):
		raise NotImplementedError()
		
	def _compute_hash(self, x:object) -> str:
		return hashlib.sha256(str(x).encode("utf-8")).hexdigest()
	
	@property
	def hash(self) -> str:
		if self._hash is None:
			self.recompute_hash()
		return self._hash