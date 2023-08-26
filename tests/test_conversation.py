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
		conv.message_sequence.replace_message(msg3, edited_msg3)

		self.assertNotEqual(conv.message_sequence.hash, initial_message_sequence_hash)
		self.assertEqual(conv.hash, conv_hash)
		
		initial_message_sequence_hash = conv.message_sequence.hash
		
		conv.message_sequence.replace_message(edited_msg3, edited_msg3)
		self.assertEqual(conv.message_sequence.hash, initial_message_sequence_hash)
		self.assertEqual(conv.hash, conv_hash)
		
if __name__ == '__main__':
	unittest.main()