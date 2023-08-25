from AbstractAI.Hashable import Hashable, hash_property

class BaseMessageSource(Hashable):
    """Base class for message sources."""

    def __init__(self):
        super().__init__()