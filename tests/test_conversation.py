import unittest
from AbstractAI.Conversation import *

class TestConversation(unittest.TestCase):
	def test_add_messages(self):
		conv = Conversation()
		user_source = UserSource()
		terminal_source = TerminalSource("test_command")

		msg1 = Message("Hello", Role.User, user_source)
		msg2 = Message("How are you?", Role.User, user_source)
		msg3 = Message("I am an AI.", Role.Assistant, terminal_source)

		conv.message_sequence.add_message(msg1)
		conv.message_sequence.add_message(msg2)
		conv.message_sequence.add_message(msg3)

		self.assertEqual(len(conv.message_sequence.messages), 3)
		self.assertEqual(conv.message_sequence.messages[0], msg1)
		self.assertEqual(conv.message_sequence.messages[1], msg2)
		self.assertEqual(conv.message_sequence.messages[2], msg3)

	def test_message_sequence_hash_changes(self):
		conv = Conversation()
		user_source = UserSource()
		terminal_source = TerminalSource("test_command")

		msg1 = Message("Hello", Role.User, user_source)
		msg2 = Message("How are you?", Role.User, user_source)
		msg3 = Message("I am an AI.", Role.Assistant, terminal_source)

		initial_hash = conv.message_sequence.hash
		conv_hash = conv.hash

		conv.message_sequence.add_message(msg1)
		self.assertNotEqual(conv.message_sequence.hash, initial_hash)
		initial_hash = conv.message_sequence.hash
		self.assertEqual(conv.hash, conv_hash)

		conv.message_sequence.add_message(msg2)
		self.assertNotEqual(conv.message_sequence.hash, initial_hash)
		initial_hash = conv.message_sequence.hash
		self.assertEqual(conv.hash, conv_hash)

		conv.message_sequence.add_message(msg3)
		self.assertNotEqual(conv.message_sequence.hash, initial_hash)
		self.assertEqual(conv.hash, conv_hash)

	def test_message_sequence_hash_changes_on_edit(self):
		conv = Conversation()
		user_source = UserSource()
		terminal_source = TerminalSource("test_command")

		msg1 = Message("Hello", Role.User, user_source)
		msg2 = Message("How are you?", Role.User, user_source)
		msg3 = Message("I am an AI.", Role.Assistant, terminal_source)

		conv.message_sequence.add_message(msg1)
		conv.message_sequence.add_message(msg2)
		conv.message_sequence.add_message(msg3)

		initial_message_sequence_hash = conv.message_sequence.hash
		conv_hash = conv.hash

		edited_msg3 = Message("I am an updated AI.", Role.Assistant, terminal_source)
		edited_msg3_2 = Message("I am an updated AI.", Role.Assistant, terminal_source)
		edited_msg3_2.creation_time = edited_msg3.creation_time
		
		conv.message_sequence.replace_message(msg3, edited_msg3)

		self.assertNotEqual(conv.message_sequence.hash, initial_message_sequence_hash)
		self.assertEqual(conv.hash, conv_hash)
		
		initial_message_sequence_hash = conv.message_sequence.hash
		
		conv.message_sequence.replace_message(edited_msg3, edited_msg3_2)
		self.assertEqual(conv.message_sequence.hash, initial_message_sequence_hash)
		self.assertEqual(conv.hash, conv_hash)
		
	def test_replace_function(self):
		conv = Conversation()
		user_source = UserSource()

		messages = [
			Message(str(i), Role.User, user_source) for i in range(1, 6)
		]

		for msg in messages:
			conv.message_sequence.add_message(msg)

		initial_message_sequence_hash = conv.message_sequence.hash
		conv_hash = conv.hash

		new_message = Message("a", Role.User, user_source)
		conv.message_sequence.replace_message(messages[2], new_message)

		self.assertEqual(len(conv.message_sequence.messages), 3)
		self.assertEqual(conv.message_sequence.messages[0], messages[0])
		self.assertEqual(conv.message_sequence.messages[1], messages[1])
		self.assertEqual(conv.message_sequence.messages[2], new_message)

		self.assertNotEqual(conv.message_sequence.hash, initial_message_sequence_hash)
		self.assertEqual(conv.hash, conv_hash)
		
	def test_altered_message_hashes(self):
		conv = Conversation()
		user_source = UserSource()

		msg1 = Message("Hello", Role.User, user_source)
		msg2 = Message("How are you?", Role.User, user_source)

		conv.message_sequence.add_message(msg1)
		conv.message_sequence.add_message(msg2)

		initial_conv_hash = conv.hash
		initial_msg_sequence_hash = conv.message_sequence.hash
		initial_msg2_hash = msg2.hash

		msg2.content = "What's up?"

		self.assertEqual(conv.hash, initial_conv_hash)
		self.assertNotEqual(msg2.hash, initial_msg2_hash)
		self.assertNotEqual(conv.message_sequence.hash, initial_msg_sequence_hash)
	
	def test_source_changes_and_hash_recomputation(self):
		conv = Conversation()
		user_source = UserSource()
		model_source = ModelSource("LargeModel", "gpt-3.5-turbo", "What is the meaning of life?")
		terminal_source = TerminalSource("test_command")
		edit_source = EditSource(None, None)

		msg = Message("Test message", Role.User, user_source)

		conv.message_sequence.add_message(msg)
		initial_hash = msg.hash

		# Change source to ModelSource
		msg.source = model_source
		self.assertNotEqual(msg.hash, initial_hash)
		initial_hash = msg.hash

		# Change a field in ModelSource
		msg.source.model_name = "NewLargeModel"
		self.assertNotEqual(msg.hash, initial_hash)
		initial_hash = msg.hash

		# Change source to TerminalSource
		msg.source = terminal_source
		self.assertNotEqual(msg.hash, initial_hash)
		initial_hash = msg.hash

		# Change a field in TerminalSource
		msg.source.command = "new_test_command"
		self.assertNotEqual(msg.hash, initial_hash)
		initial_hash = msg.hash

		# Change source to EditSource
		msg.source = edit_source
		self.assertNotEqual(msg.hash, initial_hash)
		initial_hash = msg.hash
		
if __name__ == '__main__':
	unittest.main()