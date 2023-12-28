import unittest
from AbstractAI.ConversationModel import *
from ClassyFlaskDB.DATA import DATAEngine

class TestConversation(unittest.TestCase):
	def setUp(self) -> None:
		self.engine = DATAEngine(ConversationDATA)
		return super().setUp()
	
	def test_add_messages(self):
		conv = Conversation()
		user_source = UserSource()
		terminal_source = TerminalSource("test_command")

		msg1 = Message("Hello", user_source)
		msg2 = Message("How are you?", user_source)
		msg3 = Message("Command not found", terminal_source)

		conv.add_message(msg1)
		conv.add_message(msg2)
		conv.add_message(msg3)

		self.assertEqual(len(conv.message_sequence.messages), 3)
		self.assertEqual(conv.message_sequence.messages[0], msg1)
		self.assertEqual(conv.message_sequence.messages[1], msg2)
		self.assertEqual(conv.message_sequence.messages[2], msg3)

	def test_message_sequence_id_changes(self):
		conv = Conversation()
		user_source = UserSource()
		terminal_source = TerminalSource("test_command")

		msg1 = Message("Hello", user_source)
		msg2 = Message("How are you?", user_source)
		msg3 = Message("Command not found", terminal_source)

		ms_id = conv.message_sequence.get_primary_key()
		conv_id = conv.get_primary_key()

		conv.add_message(msg1)
		self.assertNotEqual(conv.message_sequence.get_primary_key(), ms_id)
		self.assertEqual(conv.get_primary_key(), conv_id)

		conv.add_message(msg2)
		self.assertNotEqual(conv.message_sequence.get_primary_key(), ms_id)
		self.assertEqual(conv.get_primary_key(), conv_id)

		conv.add_message(msg3)
		self.assertNotEqual(conv.message_sequence.get_primary_key(), ms_id)
		self.assertEqual(conv.get_primary_key(), conv_id)

	def test_message_sequence_id_changes_on_edit(self):
		conv = Conversation()
		user_source = UserSource()
		terminal_source = TerminalSource("test_command")

		msg1 = Message("Hello", user_source)
		msg2 = Message("How are you?", user_source)
		msg3 = Message("I am an AI.", terminal_source)

		conv.add_message(msg1)
		conv.add_message(msg2)
		conv.add_message(msg3)

		initial_message_sequence_id = conv.message_sequence.get_primary_key()
		conv_id = conv.get_primary_key()

		edited_msg3 = Message("I am an updated AI.", terminal_source)
		edited_msg3_2 = Message("I am an updated AI.", terminal_source)
		edited_msg3_2.creation_time = edited_msg3.creation_time
		
		conv.message_sequence.replace_message(msg3, edited_msg3)

		self.assertNotEqual(conv.message_sequence.get_primary_key(), initial_message_sequence_id)
		self.assertEqual(conv.get_primary_key(), conv_id)
		
		initial_message_sequence_id = conv.message_sequence.get_primary_key()
		
		conv.message_sequence.replace_message(edited_msg3, edited_msg3_2)
		self.assertNotEqual(conv.message_sequence.get_primary_key(), initial_message_sequence_id)
		self.assertEqual(conv.get_primary_key(), conv_id)
		
	def test_replace_function(self):
		conv = Conversation()
		user_source = UserSource()

		messages = [
			Message(str(i), user_source) for i in range(1, 6)
		]

		for msg in messages:
			conv.add_message(msg)

		initial_message_sequence_id = conv.message_sequence.get_primary_key()
		conv_id = conv.get_primary_key()

		new_message = Message("a", user_source)
		conv.message_sequence.replace_message(messages[2], new_message)

		self.assertEqual(len(conv.message_sequence.messages), 3)
		self.assertEqual(conv.message_sequence.messages[0], messages[0])
		self.assertEqual(conv.message_sequence.messages[1], messages[1])
		self.assertEqual(conv.message_sequence.messages[2], new_message)

		self.assertNotEqual(conv.message_sequence.get_primary_key(), initial_message_sequence_id)
		self.assertEqual(conv.get_primary_key(), conv_id)
	
if __name__ == '__main__':
	unittest.main()