import hashlib

class Hashable():
	def __init__(self):
		self.hash = ""
	
	def recompute_hash(self):
		raise NotImplementedError()
		
	def _compute_hash(self, x:object) -> str:
		return hashlib.sha256(str(x).encode("utf-8")).hexdigest()
		