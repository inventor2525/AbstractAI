from AbstractAI.Conversation import *

es = EditSource(None, None)
print(es.hash)
es.original = Message("content", Role.Assistant)
ct = es.original.creation_time
print(es.hash)

es.original = Message("content", Role.Assistant)
print(es.hash)

es.original = Message("content", Role.Assistant)
es.original.creation_time = ct
print(es.hash)