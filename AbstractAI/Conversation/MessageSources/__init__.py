from AbstractAI.Hashable import Hashable
from UserSource import UserSource
from ModelSource import ModelSource
from EditSource import EditSource
from TerminalSource import TerminalSource

class BaseMessageSource(Hashable):
	"""Base class for message sources."""

	def __init__(self):
		pass