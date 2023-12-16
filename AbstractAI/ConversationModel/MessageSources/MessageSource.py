from AbstractAI.ConversationModel.ModelBase import *

@DATA
class MessageSource:
    """
    Base class for message sources.
    
    These will contain information about where a message came from.
    """
    system_message: bool = field(default=False, kw_only=True)