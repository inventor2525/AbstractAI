from typing import Tuple
from AbstractAI.Model.Converse.MessageSources import *
from enum import Enum

class CommonRoles(Enum):
	'''
	Useful to fudge a 'Role' from a Object.
	
	Normally, such specific roles should not be enforced for general use
	models that interact with systems or other models and not just people.
	But some models may prefer the formatting or respond overly better to
	these common roles.
	'''
	System = "system"
	User = "user"
	Assistant = "assistant"
	
	def from_source(source:Object) -> Tuple["CommonRoles", str]:
		role = CommonRoles.User
		name = None
		
		if source:
			if isinstance(source, EditSource):
				source = source.original_source()
			if source.system_message:
				role = CommonRoles.System
			elif isinstance(source, UserSource):
				role = CommonRoles.User
				name = source.user_name
			elif isinstance(source, ModelSource):
				role = CommonRoles.Assistant
			elif isinstance(source, TerminalSource):
				role = CommonRoles.User
				name = "terminal"
		
		return role, name