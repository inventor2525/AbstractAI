from ClassyFlaskDB.DefaultModel import *
from AbstractAI.Model.Converse import *

engine = DATAEngine(DATA)

stack_trace = CallerInfo.catch()
conv = Conversation("A great conversation")
conv + ("Hello computer",Role.User()) | stack_trace

print(conv)
print(conv.source)
print(conv[-1].source)

conv + ("Hello human!",Role.Assistant()) | stack_trace



print(conv[-1].content)
print(conv[-1].role)
print(conv[-1].source)

print(conv)