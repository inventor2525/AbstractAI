from AbstractAI.Model.Decorator import *
from AbstractAI.Model.Converse.MessageSources.CallerInfo import CallerInfo

@DATA
@dataclass
class MessageSource:
	"""
	Base class for message sources.
	
	These will contain information about where a message came from.
	"""
	system_message: bool = field(default=False, kw_only=True)
	
	caller_source: CallerInfo = field(default_factory=lambda:CallerInfo.get_caller_info(extra_up=2), kw_only=True)

def SystemSource() -> MessageSource:
	return MessageSource(system_message=True)