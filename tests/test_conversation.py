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

if __name__ == '__main__':
    unittest.main()