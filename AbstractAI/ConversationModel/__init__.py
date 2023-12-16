from .MessageSources import MessageSource, UserSource, ModelSource, EditSource, TerminalSource
from .Message import Message
from .Conversation import Conversation, MessageSequence
from .ConversationCollection import ConversationCollection
from .ModelBase import DATA

def print_conversation(conversation:Conversation):
	import json
	from ClassyFlaskDB.Flaskify.serialization import FlaskifyJSONEncoder
	
	print("=====================================")
	for message in conversation.message_sequence.messages:
		print(f"{message.creation_time.strftime('%Y-%m-%d %H:%M:%S')} source: {type(message.source).__name__}")
		print(message.content)
		print()
	print("=====================================")
	print(json.dumps(conversation.to_json(), indent=4, cls=FlaskifyJSONEncoder))
	print("=====================================")