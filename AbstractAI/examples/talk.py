from AbstractAI.ApplicationCore import *

app = ApplicationCore("/home/charlie/Documents/AbstractAI")
llm = app["llama 3.1 70b"]

conversation = Conversation()
@app.llm_method(llm, with_history=True)
def chat(conv:Conversation, msg:str) -> ResponseObject:
	return msg

try:
	for transcription in app.transcribe_live():
		print(f"Transcribed: '{transcription.text}' at {datetime.now()}")
		ro = chat(conversation, transcription.text)
		
		print("Speaking...")
		with app.vad.pauser():
			app.speak(str(ro), blocking=True)
		print("Done speaking!")
	print("Exited transcription loop")
		
except KeyboardInterrupt:
	print("Stopping transcription...")