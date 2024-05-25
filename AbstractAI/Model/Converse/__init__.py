from .MessageSources import UserSource, ModelSource, EditSource, FilesSource
from .Message import Message
from .Conversation import Conversation, MessageSequence
from .ConversationCollection import ConversationCollection
from ClassyFlaskDB.DefaultModel import *

def print_conversation(conversation:Conversation):
	import json
	from AbstractAI.Helpers.JSONEncoder import JSONEncoder
	
	print("=====================================")
	for message in conversation.message_sequence.messages:
		print(f"{message.date_created.strftime('%Y-%m-%d %H:%M:%S')} source: {type(message.source).__name__}")
		print(message.content)
		print()
	print("=====================================")
	print(json.dumps(conversation.to_json(), indent=4, cls=JSONEncoder))
	print("=====================================")