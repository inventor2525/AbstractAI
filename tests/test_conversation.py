import unittest
from AbstractAI.Model.Converse import *
from ClassyFlaskDB.DATA import DATAEngine, print_DATA_json

class TestConversation(unittest.TestCase):
	def setUp(self) -> None:
		self.engine = DATAEngine(DATA)
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
		edited_msg3_2.date_created = edited_msg3.date_created
		
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
	
	def test_edit_message(self):
		conv = Conversation()
		user_source = UserSource("Test User")
		terminal_source = TerminalSource("test_command")
		
		msg1 = Message.HardCoded("Hello, World!", system_message=True)
		msg2 = Message("How are you?", user_source)
		msg3 = Message("Command not found", terminal_source)
		
		conv.add_message(msg1)
		conv.add_message(msg2)
		conv.add_message(msg3)
		
		self.assertEqual(msg1.prev_message, None)
		self.assertEqual(msg2.prev_message, msg1)
		self.assertEqual(msg3.prev_message, msg2)
		
		initial_message_sequence_id = conv.message_sequence.get_primary_key()
		conv_id = conv.get_primary_key()
		
		edited_msg3 = Message.create_edited(msg1, "Hello world...", source_of_edit=user_source)
		conv.message_sequence.replace_message(msg1, edited_msg3, True)
		
		self.assertEqual(len(conv.message_sequence.messages), 3)
		self.assertEqual(conv.message_sequence.messages[0], edited_msg3)
		self.assertEqual(conv.message_sequence.messages[1], msg2)
		self.assertEqual(conv.message_sequence.messages[2], msg3)
		
		self.assertNotEqual(conv.message_sequence.get_primary_key(), initial_message_sequence_id)
		self.assertEqual(conv.get_primary_key(), conv_id)
		
		self.assertEqual(edited_msg3.prev_message, None)
		self.assertEqual(edited_msg3.source.original, msg1)
		self.assertEqual(edited_msg3.source.new, edited_msg3)
		
		self.assertEqual(msg1.prev_message, None)
		self.assertEqual(msg2.prev_message, msg1)
	
	def test_to_json(self):
		conv = Conversation()
		user_source = UserSource()
		terminal_source = TerminalSource("test_command")

		msg1 = Message.HardCoded("Hello", system_message=True)
		msg2 = Message("How are you?", user_source)
		msg3 = Message("Command not found", terminal_source)
		
		conv.add_message(msg1)
		conv.add_message(msg2)
		conv.add_message(msg3)
		
		self.assertEqual(msg1.prev_message, None)
		self.assertEqual(msg2.prev_message, msg1)
		self.assertEqual(msg3.prev_message, msg2)
		
		conv_json = conv.to_json()
		self.assertIsInstance(conv_json, dict)
		self.assertEqual(len(conv_json), 3)
		
		self.assertEqual(conv_json["primary_key"], conv.get_primary_key())
		self.assertEqual(conv_json["type"], "Conversation")
		self.assertIsInstance(conv_json["obj"], dict)
		
		print_DATA_json(conv_json)
		
		self.assertEqual(len(conv_json["obj"]["CallerInfo_Table"]), 1)
		self.assertEqual(len(conv_json["obj"]["Conversation_Table"]), 1)
		self.assertEqual(len(conv_json["obj"]["EditSource_Table"]), 0)
		self.assertEqual(len(conv_json["obj"]["HardCodedSource_Table"]), 1)
		self.assertEqual(len(conv_json["obj"]["MessageSequence_Table"]), 1)
		self.assertEqual(len(conv_json["obj"]["MessageSequence_messages_mapping"]), 3)
		self.assertEqual(len(conv_json["obj"]["MessageSource_Table"]), 3)
		self.assertEqual(len(conv_json["obj"]["ModelSource_Table"]), 0)
		self.assertEqual(len(conv_json["obj"]["Message_Table"]), 3)
		self.assertEqual(len(conv_json["obj"]["TerminalSource_Table"]), 1)
		self.assertEqual(len(conv_json["obj"]["UserSource_Table"]), 1)
		
		json_messages = {msg_json["content"]:msg_json for msg_json in conv_json["obj"]["Message_Table"]}
		json_messages_by_key = {msg_json["auto_id"]:msg_json for msg_json in conv_json["obj"]["Message_Table"]}
		
		self.assertEqual(json_messages["Hello"]["prev_message_fk"], None)
		self.assertEqual(json_messages_by_key.get(json_messages["Hello"]["prev_message_fk"], None), None)
		self.assertEqual(json_messages_by_key.get(json_messages["How are you?"]["prev_message_fk"], None), json_messages["Hello"])
		self.assertEqual(json_messages_by_key.get(json_messages["Command not found"]["prev_message_fk"], None), json_messages["How are you?"])
	
	def test_to_from_json(self):
		conv = Conversation()
		user_source = UserSource()
		terminal_source = TerminalSource("test_command")

		msg1 = Message.HardCoded("Hello", system_message=True)
		msg2 = Message("How are you?", user_source)
		msg3 = Message("Command not found", terminal_source)
		
		conv.add_message(msg1)
		conv.add_message(msg2)
		conv.add_message(msg3)
		
		self.assertEqual(msg1.prev_message, None)
		self.assertEqual(msg2.prev_message, msg1)
		self.assertEqual(msg3.prev_message, msg2)
		
		conv_json = conv.to_json()
		print_DATA_json(conv_json)
		
		conv2 = Conversation.from_json(conv_json)
		self.assertEqual(conv2.get_primary_key(), conv.get_primary_key())
		self.assertEqual(len(conv2.message_sequence.messages), len(conv.message_sequence.messages))
		for message1, message2 in zip(conv.message_sequence.messages, conv2.message_sequence.messages):
			self.assertEqual(message1.prev_message, message2.prev_message)
			self.assertEqual(message1.source, message2.source)
			self.assertEqual(message1.conversation, message2.conversation)
			
			self.assertEqual(message1.get_primary_key(), message2.get_primary_key())
			
			self.assertEqual(message1.content, message2.content)
			
			if message1.source is not None:
				self.assertEqual(message1.source.get_primary_key(), message2.source.get_primary_key())
			
			if message1.prev_message is not None:
				self.assertEqual(message1.prev_message.get_primary_key(), message2.prev_message.get_primary_key())
				
			if message1.conversation is not None:
				self.assertEqual(message1.conversation.get_primary_key(), message2.conversation.get_primary_key())
	
	def test_alternates(self):
		conv = Conversation()
		user_source = UserSource()
		
		messages = [
			Message(str(i), user_source) for i in range(1, 6)
		]
		
		all_sequences = [conv.message_sequence]
		alternates_ground_truth = []
		for index, msg in enumerate(messages):
			conv.add_message(msg)
			all_sequences.append(conv.message_sequence)
			if index >= 2:
				alternates_ground_truth.append(conv.message_sequence)
		
		alternates = conv.alternates(messages[2])
		self.assertEqual(len(alternates), len(alternates_ground_truth))
		for real_alt, alt in zip(alternates_ground_truth, alternates):
			self.assertEqual(real_alt.get_primary_key(), alt.get_primary_key())
			
		alternates = conv.alternates(None)
		self.assertEqual(len(alternates), len(all_sequences))
		for real_alt, alt in zip(all_sequences, alternates):
			self.assertEqual(real_alt.get_primary_key(), alt.get_primary_key())
		
if __name__ == '__main__':
	unittest.main()