from AbstractAI.Conversation import *

es = EditSource(None, None)
print(es.hash)
es.original = Message("content", "role")
ct = es.original.creation_time
print(es.hash)

es.original = Message("content", "role")
print(es.hash)

es.original = Message("content", "role")
es.original.creation_time = ct
es.original.recompute_hash()
print(es.hash)