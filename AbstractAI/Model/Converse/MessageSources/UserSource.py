from ClassyFlaskDB.DefaultModel import *

DefaultUser = "User"

@DATA
@dataclass
class UserSource(Object):
	'''Describes the source of a message from a person.'''
	user_name: str = field(default=DefaultUser, kw_only=True)