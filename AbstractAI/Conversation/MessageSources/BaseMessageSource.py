from AbstractAI.Hashable import Hashable, hash_property

class BaseMessageSource(Hashable):
    """
    Base class for message sources.
    
    These will contain information about where a message came from.
    """

    def __init__(self):
        super().__init__()