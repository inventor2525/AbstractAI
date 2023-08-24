from enum import Enum
from .MessageSources import BaseMessageSource, UserSource, ModelSource, EditSource, TerminalSource

class Role(Enum):
	System = "system"
	User = "user"
	Assistant = "assistant"

class Message:
	def __init__(self, content: str, role: Role, source: BaseMessageSource = None):
		self.content = content
		self.role = role
		self.source = source