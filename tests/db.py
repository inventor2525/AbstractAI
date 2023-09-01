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

m1 = db.get_message(msg1.hash)
m2 = db.get_message(msg2.hash)
m3 = db.get_message(msg3.hash)

assert m1.content == "Hello"
assert m2.content == "How are you?"
assert m3.content == "I am an AI."