from AbstractAI.ApplicationCore import *
from AbstractAI.Helpers.TerminalClient import *
from time import sleep

app = ApplicationCore("/home/charlie/Documents/AbstractAI")
llm = app["Sonnet 3.6"]

# Reload or create the conversation:
conversation_name = "Terminal Playing v1"
try:
	conversation = list(AppContext.engine.query(Conversation).all(where=f"name='{conversation_name}'"))[0]
	print("Loaded conversation!")
except:
	print("Conversation not created yet, making it...")
	conversation = Conversation(name=conversation_name)
	conversation + (TextFileArtifact("Playing/SystemPrompt.txt"), Role.System())

# Define a chat function:
@app.llm_method(llm, with_history=True)
def chat(conv:Conversation, msg:str) -> ResponseObject:
	return msg

TerminalFLASKIFY.make_client('localhost', 7788)
terminal = Terminal("My first terminal")

# Talk back and forth (with a terminal):
try:
	for transcription in app.transcribe_live():
		with app.vad.pauser():
			ro = chat(conversation, transcription.text)
			print("================================")
			response = str(ro)
			print(response)
			if response.startswith("send to terminal\n```bash\n") and response.endswith("\n```"):
				print("------------")
				response = response[len("send to terminal\n```bash\n"):-3]
				print(response)
				print("================================")
				
				lines = response.split('\n')
				for line_number, line in enumerate(lines):
					if line_number < len(lines)-1:
						line = line+"\n"
					print("---",line)
					terminal.send_string(line)
					
					sleep(1)
				sleep(1)
				ro = chat(conversation, f"# Terminal says:\n{terminal.getScreenDump().raw_text}")
				print(str(ro))
			app.speak(str(ro), blocking=True)
		
except KeyboardInterrupt:
	print("Terminating application...")
	app.quit()
	print("Goodbye!")