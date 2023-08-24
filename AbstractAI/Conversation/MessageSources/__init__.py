from datetime import datetime

class BaseMessageSource:
    """Base class for message sources."""

    def __init__(self):
        # The date time the message was created
        self.creation_time: datetime = datetime.now()