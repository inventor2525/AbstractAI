from enum import Enum

class Role(Enum):
	System = "system"
	User = "user"
	Assistant = "assistant"

class Message:
	def __init__(self, content: str, role: Role, source=None):
		self.content = content
		self.role = role
		self.source = source