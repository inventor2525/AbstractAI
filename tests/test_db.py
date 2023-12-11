import unittest
from AbstractAI.ConversationModel import *
from AbstractAI.DB.Database import Database
from typing import Callable
# Compare functions
def both_none_or_condition(obj1, obj2, condition:Callable[[object, object], bool]) -> bool:
	if obj1 is None:
		if obj2 is None:
			return True
		else:
			return False
	if obj2 is None:
		return False
	return condition(obj1,obj2)
	
def compare_hashable(obj1, obj2):
	if not both_none_or_condition(obj1,obj2, lambda o1, o2: o1.hash == o2.hash):
		return False
	return True

def compare_conversations(conv1, conv2):
	if not compare_hashable(conv1, conv2):
		return False
	if conv1.creation_time != conv2.creation_time:
		return False
	if conv1.name != conv2.name:
		return False
	if conv1.description != conv2.description:
		return False
	if not compare_hashable(conv1.message_sequence, conv2.message_sequence):
		return False
	return True

def compare_messages(msg1, msg2):
	if not compare_hashable(msg1, msg2):
		return False
	if msg1.creation_time != msg2.creation_time:
		return False
	if msg1.content != msg2.content:
		return False
	if msg1.role != msg2.role:
		return False
	if not compare_hashable(msg1.source, msg2.source):
		return False
	if not compare_hashable(msg1.prev_message, msg2.prev_message):
		return False
	if not compare_hashable(msg1.conversation, msg2.conversation):
		return False
	return True

def compare_message_sequences(ms1, ms2):
	if not compare_hashable(ms1, ms2):
		return False
	if len(ms1.messages) != len(ms2.messages):
		return False
	for msg1, msg2 in zip(ms1.messages, ms2.messages):
		if msg1.hash != msg2.hash:
			return False
	return True

def compare_sources(src1, src2):
	if not compare_hashable(src1, src2):
		return False
	if src1.__class__ != src2.__class__:
		return False
	if isinstance(src1, UserSource):
		if src1.user_name != src2.user_name:
			return False
		return True
	if isinstance(src1, TerminalSource):
		if src1.command != src2.command:
			return False
		return True
	if isinstance(src1, EditSource):
		if not compare_hashable(src1.original, src2.original):
			return False
		if not compare_hashable(src1.new, src2.new):
			return False
		return True
	if isinstance(src1, ModelSource):
		if src1.class_name != src2.class_name:
			return False
		if src1.model_name != src2.model_name:
			return False
		if src1.other_parameters != src2.other_parameters:
			return False
		if not compare_hashable(src1.message_sequence, src2.message_sequence):
			return False
		if not both_none_or_condition(src1.models_serialized_raw_output, src2.models_serialized_raw_output, lambda o1, o2: o1 == o2):
			return False
		return True
	return False
	
# Test class

class TestDB(unittest.TestCase):
	def test_db_operations(self):
		db = Database("sqlite:///test.sql")

		# Create a mock conversation
		conv = Conversation()
		user_source = UserSource()
		terminal_source = TerminalSource("test_command")

		msg1 = Message("Hello", Role.User, user_source)
		msg2 = Message("How are you?", Role.User, user_source)
		msg3 = Message("I am an AI.", Role.Assistant, terminal_source)

		msg3_new = Message("I am Not an AI.", Role.Assistant)
		msg3_new.source = EditSource(msg3, msg3_new)

		conv.message_sequence.add_message(msg1)
		conv.message_sequence.add_message(msg2)
		conv.message_sequence.add_message(msg3)

		# Save the conversation to the database
		db.add_conversation(conv)
		db.add_message(msg3_new)

		# Load the conversation from the database
		loaded_conv = db.get_conversation(conv.hash)

		# Compare the loaded conversation with the original
		self.assertTrue(compare_conversations(conv, loaded_conv))

		# Compare the message sequences
		self.assertTrue(compare_message_sequences(conv.message_sequence, loaded_conv.message_sequence))

		# Compare the messages and their sources
		for orig_msg, loaded_msg in zip(conv.message_sequence.messages, loaded_conv.message_sequence.messages):
			self.assertTrue(compare_messages(orig_msg, loaded_msg))
			self.assertTrue(compare_sources(orig_msg.source, loaded_msg.source))
	
	def test_multiple_conversations(self):
		db = Database("sqlite:///test.sql")

		# Create mock conversations
		conv1 = Conversation(name="Conv1")
		conv2 = Conversation(name="Conv2")

		user_source = UserSource()
		terminal_source = TerminalSource("test_command")

		msg1 = Message("Hello", Role.User, user_source)
		msg2 = Message("How are you?", Role.User, user_source)
		msg3 = Message("I am an AI.", Role.Assistant, terminal_source)

		conv1.message_sequence.add_message(msg1)
		conv1.message_sequence.add_message(msg2)

		conv2.message_sequence.add_message(msg3)

		# Save the conversations to the database
		db.add_conversation(conv1)
		db.add_conversation(conv2)

		# Load the conversations from the database
		loaded_conv1 = db.get_conversation(conv1.hash)
		loaded_conv2 = db.get_conversation(conv2.hash)

		# Compare the loaded conversations with the original ones
		self.assertTrue(compare_conversations(conv1, loaded_conv1))
		self.assertTrue(compare_conversations(conv2, loaded_conv2))

if __name__ == "__main__":
	unittest.main()