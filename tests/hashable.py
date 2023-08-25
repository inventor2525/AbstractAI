from AbstractAI.Conversation import *

es = EditSource(None, None)
print(es.hash)
es.original = Message("content", "role")

print(es.hash)

es.original = Message("content", "role")
print(es.hash)