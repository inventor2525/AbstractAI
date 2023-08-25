from .BaseMessageSource import BaseMessageSource, hash_property

class TerminalSource(BaseMessageSource):
	"""
	Describes the source of a message from a terminal command result.
	
	Messages with this source came from the terminal result of
	running a command.
	"""

	def __init__(self, command: str):
		super().__init__()
		# The command passed to the terminal that generated this message.
		self.command: str = command
		
	def recompute_hash(self):
		self._hash = self._compute_hash(self.command)