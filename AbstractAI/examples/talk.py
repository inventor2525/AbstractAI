from AbstractAI.ApplicationCore import *

app = ApplicationCore("/home/charlie/Documents/AbstractAI")
llm = app["llama 3.1 70b"]

conversation = Conversation()
@app.llm_method(llm, with_history=True)
def chat(conv:Conversation, msg:str) -> ResponseObject:
	return msg

try:
	for transcription in app.transcribe_live():
		print(f"Transcribed: '{transcription.transcription}' at {datetime.now()}")
		ro = chat(conversation, transcription.transcription)
		app.speak(str(ro))
		
except KeyboardInterrupt:
	print("Stopping transcription...")