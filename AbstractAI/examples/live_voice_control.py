from AbstractAI.ApplicationCore import *

app = ApplicationCore("/home/charlie/Documents/AbstractAI")

try:
	for transcription in app.transcribe_live():
		print(f"Transcribed: '{transcription.text}' at {datetime.now()}")
		
		t = transcription.text.lower().strip()
		if t.startswith("hey computer"):
			print("Hey what?!")
			break
		
	for transcription in app.transcribe_live():
		print(f"Transcribed: '{transcription.text}' at {datetime.now()}")
		
		t = transcription.text.lower().strip()
		if t.startswith("exit"):
			break

except KeyboardInterrupt:
	print("Stopping transcription...")

print("Transcription stopped.")