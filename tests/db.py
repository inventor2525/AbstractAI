from AbstractAI.DB.Database import *

db = Database("sqlite:///test.sql")

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

db.add_conversation(conv)
db.add_message(msg3_new)

m1 = db.get_message(msg1.hash)
m2 = db.get_message(msg2.hash)
m3 = db.get_message(msg3.hash)
m3_ = db.get_message(msg3_new.hash)

assert m1.content == "Hello"
assert m2.content == "How are you?"
assert m3.content == "I am an AI."