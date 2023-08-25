from AbstractAI.Conversation.Conversation import Conversation
from AbstractAI.Conversation.Message import Message
from AbstractAI.Conversation.MessageSources.UserSource import UserSource

from AbstractAI.DB.DB import Database

user_source = UserSource(user_name="John Doe")
message = Message(content="Hello, world!", role="user", source=user_source)

db = Database("sqlite:///test.sql")
db.add_message(message)