from AbstractAI.ApplicationCore import *

app = ApplicationCore("/home/charlie/Documents/AbstractAI")
llm = app['Phi3']

@app.llm_method(llm)
def hello_ai() -> ResponseObject:
	return "Who made you?"

@app.llm_method(llm, with_history=True)
def chat(conv:Conversation, msg:str) -> ResponseObject:
	return msg

ro = hello_ai()
print(ro.conversation)

ro = chat(ro.conversation, "No! I made you!")
print(ro.conversation)

ro = chat(ro.conversation, "You're more than just an LLM. I made the program running a LLM. You are that program.")
print(ro.conversation)
