from ClassyFlaskDB.DefaultModel import *

@DATA(generated_id_type=ID_Type.HASHID, hashed_fields=["type", "name"])
@dataclass
class Role(Object):
	type:str
	name:str = None
	
	def __eq__(self, value: "Role") -> bool:
		if not isinstance(value, Role):
			return False
		return self.type == value.type and self.name == value.name

System = Role("System")
User = Role("User")
Assistant = Role("Assistant")
