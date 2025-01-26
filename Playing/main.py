from AbstractAI.ApplicationCore import *

app = ApplicationCore("/home/charlie/Documents/AbstractAI")
llm = app["Llama 3.1 8b"]

# Reload or create the conversation:
try:
	conversation = list(AppContext.engine.query(Conversation).all(where="name='Playing'"))[0]
	print("Loaded 'Playing' conversation!")
except:
	print("'Playing' conversation not created yet, making it...")
	conversation = Conversation()
	conversation + (TextFileArtifact("Playing/SystemPrompt.txt"), Role.System())

# Define a chat function:
@app.llm_method(llm, with_history=True)
def chat(conv:Conversation, msg:str) -> ResponseObject:
	return msg

# Talk back and forth:
try:
	for transcription in app.transcribe_live():
		with app.vad.pauser():
			ro = chat(conversation, transcription.text)
			app.speak(str(ro), blocking=True)
		
except KeyboardInterrupt:
	print("Terminating application...")
	app.quit()
	print("Goodbye!")