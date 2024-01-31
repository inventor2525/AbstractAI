from AbstractAI.ConversationModel import *
from AbstractAI.LLMs.LLamaCPP_LLM import *
from ClassyFlaskDB.DATA import *

engine = DATAEngine(ConversationDATA, engine_str='sqlite:///:memory:')
model = LLamaCPP_LLM(
	"Mixtral", "/home/charlie/Projects/text-generation-webui/models/mixtral-8x7b-instruct-v0.1.Q4_K_M.gguf",
	parameters={ "generate":{"max_tokens":64} })
model.start()

modelSource = ModelSource(model_info=ModelInfo(class_name="Fake class", model_name="Fake model"))
userSource = UserSource("User")

conv = Conversation()
conv.add_message(Message("Hello, how are you?", source=userSource))
conv.add_message(Message("I am an AI, I don't have a state of well-being.", source=modelSource))
conv.add_message(Message("Ok... How are you ?thinking? then I guess?", source=userSource))
conv.add_message(Message("I am an AI, I do not think. I convert our conversation to a single text containing our messages formatted in a clever format and then predict what might come next in that text for only the role that I am playing. There is no intelligence involved, I am not even a being, just a token predictor that has been given a clever format to coax me into looking like I am talking to you.", source=modelSource))
conv.add_message(Message("Um... what are you predicting now then?", source=userSource))
# conv.add_message(Message("That you don't have a problem I can assist you with.", source=modelSource))
# conv.add_message(Message("Interesting.", source=userSource))

engine.merge(conv)

response = model.chat(conv, "This conversation is boaring, do you have an actual problem I can assist you")
conv.add_message(response.message)
engine.merge(conv)
print(response.message.content)


while True:
	input_str = input(">> ")
	if input_str == "exit":
		break
	conv.add_message(Message(input_str, source=userSource))
	engine.merge(conv)
	
	response = model.chat(conv)
	conv.add_message(response.message)
	engine.merge(conv)
	
	print(response.message.content)