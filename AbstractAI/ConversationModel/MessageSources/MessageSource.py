from AbstractAI.ConversationModel.ModelBase import *
from AbstractAI.ConversationModel.MessageSources.CallerInfo import CallerInfo

@ConversationDATA
class MessageSource:
    """
    Base class for message sources.
    
    These will contain information about where a message came from.
    """
    system_message: bool = field(default=False, kw_only=True)
    
    caller_source: CallerInfo = field(default_factory=CallerInfo.get_caller_info, kw_only=True)