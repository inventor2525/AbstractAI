from AbstractAI.DB.Database import *

db = Database("sqlite:///test.sql")

conv = Conversation()
user_source = UserSource()
terminal_source = TerminalSource("test_command")

msg1 = Message("Hello", Role.User, user_source)
msg2 = Message("How are you?", Role.User, user_source)
msg3 = Message("I am an AI.", Role.Assistant, terminal_source)

conv.message_sequence.add_message(msg1)
conv.message_sequence.add_message(msg2)
conv.message_sequence.add_message(msg3)

db.add_conversation(conv)