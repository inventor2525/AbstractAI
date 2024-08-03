from ClassyFlaskDB.DefaultModel import *
from functools import wraps

def singleton(method):
    instances = {}
    @wraps(method)
    def wrapper(*args, **kwargs):
        if method.__name__ not in instances:
            instances[method.__name__] = method(*args, **kwargs)
        return instances[method.__name__]
    return wrapper

@DATA(id_type=ID_Type.HASHID, hashed_fields=["type", "name"])
@dataclass
class Role(Object):
	type:str
	name:str = None
	
	def __eq__(self, value: "Role") -> bool:
		if not isinstance(value, Role):
			return False
		return self.type == value.type and self.name == value.name
	
	@singleton
	@staticmethod
	def System() -> "Role":
		return Role("System")
	
	@singleton
	@staticmethod
	def User() -> "Role":
		return Role("User")
	
	@singleton
	@staticmethod
	def Assistant() -> "Role":
		return Role("Assistant")
	
	@singleton
	@staticmethod
	def Tool() -> "Role":
		return Role("Tool")
	
	def __str__(self) -> str:
		if self.name:
			return f"{self.type} ({self.name})"
		return self.type