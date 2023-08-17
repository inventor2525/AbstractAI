from enum import Enum

class Role(Enum):
	SYSTEM = "system"
	USER = "user"
	ASSISTANT = "assistant"

class Message:
	def __init__(self, content: str, role: Role, source=None):
		self.content = content
		self.role = role
		self.source = source