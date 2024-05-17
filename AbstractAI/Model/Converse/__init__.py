from .MessageSources import MessageSource, UserSource, ModelSource, EditSource, TerminalSource, HardCodedSource, SystemSource, FilesSource
from .Message import Message
from .Conversation import Conversation, MessageSequence
from .ConversationCollection import ConversationCollection
from .ModelBase import DATA, get_local_time

def print_conversation(conversation:Conversation):
	import json
	from AbstractAI.Helpers.JSONEncoder import JSONEncoder
	
	print("=====================================")
	for message in conversation.message_sequence.messages:
		print(f"{message.creation_time.strftime('%Y-%m-%d %H:%M:%S')} source: {type(message.source).__name__}")
		print(message.content)
		print()
	print("=====================================")
	print(json.dumps(conversation.to_json(), indent=4, cls=JSONEncoder))
	print("=====================================")