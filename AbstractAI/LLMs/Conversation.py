from .Message import Message
from typing import List
class Conversation:
    def __init__(self):
        self.messages:List[Message] = []

    def add_message(self, message: Message):
        self.messages.append(message)