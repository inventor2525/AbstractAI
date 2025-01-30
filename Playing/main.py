from AbstractAI.ApplicationCore import *
from AbstractAI.Helpers.TerminalClient import *
from AbstractAI.Helpers.ResponseParsers import MarkdownCodeBlockInfo, extract_code_blocks
from time import sleep
import codecs

# Start the application and load the LLM:
app = ApplicationCore("/home/charlie/Documents/AbstractAI")
llm = app["Sonnet 3.6"]

# Reload or create the conversation:
conversation_name = "Terminal Playing v5"
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
	'''
	Simply returns the message the user would like added to the
	conversation and sent to the passed LLM. The decorator handles
	most of the work.
	'''
	return msg

# Connect to a pty/remote terminal emulator application
# (This accepts full VT100 string io even including escape sequences
# for things like the escape key, and can return a screen buffer
# or all stdout from the PTY, including screen redraw commands):
TerminalFLASKIFY.make_client('localhost', 7788)
terminal = Terminal("My first terminal")

def do(items:List[Union[str, MarkdownCodeBlockInfo]]):
	'''
	Execute the instructions of a list of parsed markdown code blocks.
	
	Either saves those that were prefaced with a path, or runs those bash
	ones that were not.
	'''
	status_to_bot = []
	def send_to_terminal(code_block_content:str) -> str:
		lines = code_block_content.split('\n')
		for line_number, line in enumerate(lines):
			line = codecs.escape_decode(line)[0].decode('utf-8')
			terminal.send_string(line)
			sleep(1)
		terminal_screen_dump = terminal.getScreenDump().raw_text
		return f"Terminal screen shows this after bash block:\n```txt\n{terminal_screen_dump}\n```"
	
	def save(content:str, path:str) -> str:
		try:
			with open(item.path, 'w', encoding='utf-8') as file:
				file.write(item.content)
			return f"File saved at {item.path} successfully!"
		except Exception as e:
			return f"Failed to save file at {item.path} with exception: {str(e)}"
	
	for item in items:
		if isinstance(item, MarkdownCodeBlockInfo):
			if item.path is not None:
				status = save(item.content, item.path)
			elif item.language == 'bash':
				status = send_to_terminal(item.content)
			else:
				status = "A markdown code block was sent without a full path on the line before it (with no other text on that line), or it being a bash block. Such code blocks can not be processed."
			status_to_bot.append(status)
	return status_to_bot
				
def any_in(items:Iterable[str], string:str) -> bool:
	for item in items:
		if item in string:
			return True
	return False

code_blocks = extract_code_blocks(conversation[-1].content)

# Talk loop between human, AI, terminal and file save operations:
status_to_bot = []
try:
	transcriptions = app.transcribe_live()

	is_listening = True

	un_sent = ""
	
	while True:
		# Get the next thing the user said from the
		# voice activity detector + transcriber pair:
		transcription = next(transcriptions)
		
		# Check for pause/resume listening commands:
		if 'stop listening' == transcription.text.lower():
			is_listening = False
			with app.vad.pauser():
				app.speak("No longer listening.")
			continue
		elif 'start listening' == transcription.text.lower():
			is_listening = True
			with app.vad.pauser():
				app.speak("I'm listening again!")
			continue

		# Only accumulate text if we're listening:
		if not is_listening:
			continue
		
		# Just keep listening until they tell us to send:
		if 'send message now' not in transcription.text.lower():
			un_sent += transcription.text
			continue
		
		with app.vad.pauser():
			# Send what the user said to the bot, along with
			# anything the application still needs to tell the bot:
			if len(status_to_bot)==0:
				response_obj = chat(conversation, un_sent)
			else:
				bullets = [f'- {s}' for s in status_to_bot]
				bullets = '\n'.join(bullets)
				to_bot = f"First, here are some things from the application you should know:\n{bullets}\nThen, here is what the user said:\n\"{un_sent}\""
				response_obj = chat(conversation, to_bot)
				status_to_bot.clear()
			response = str(response_obj)
			un_sent = ""
			
			# Speak to the user what it is the AI said to the user,
			# and a summary of what it is instructing the application to do:
			to_speak = []
			has_tasks_to_confirm = False
			items = extract_code_blocks(response) # Gets markdown code blocks separated by the text between them.
			for item in items:
				if isinstance(item, str):
					to_speak.append(item)
				elif isinstance(item, MarkdownCodeBlockInfo):
					if item.path is not None: #The path that was given on the line before the codeblock (if a path was given)
						# Speak the path of the file we're going to write over
						# /path/to/file.ext as "file.ext, inside: to, inside: path":
						spoken_path = item.path.split('/')
						if len(spoken_path)>1 and len(spoken_path[0])==0:
							spoken_path = spoken_path[1:]
						spoken_path = ", inside: ".join(reversed(spoken_path))
						to_speak.append(f"Save {item.language} file to: {spoken_path}")
						has_tasks_to_confirm = True
					elif item.language == 'bash':
						to_speak.append("Run a given bash script.")
						has_tasks_to_confirm = True
						#TODO: describe the bash script with a separate call to a different LLM
						#(Need the conversation for it to be hidden in the UI)
					else:
						to_speak.append(f"There's a {item.language} code block with no path.")
			
			# Join together all things that need to be spoken,
			# and ask the user for confirmation if appropriate:
			to_speak = "\n\nThen, after that:\n".join(to_speak)
			if has_tasks_to_confirm:
				to_speak += "\n\nWould you like to perform these actions? Yes or no?"
			app.speak(to_speak)
		
		# Confirm with the user that they do indeed want to do those things:
		if has_tasks_to_confirm:
			while True:
				transcription = next(transcriptions)
				with app.vad.pauser():
					lower_transcription = transcription.text.lower()
					if 'no' in lower_transcription:
						app.speak("Ok, I wont. What now then?")
						status_to_bot.append("The user has rejected all actions you just attempted to make. No bash blocks were run and no file save operations have ocurred.")
						break
					elif 'yes' in lower_transcription:
						status_to_bot.extend(do(items))
						app.speak("Done!")
						break
					elif any_in([
						'repeat that',
						'What did you say',
						"what'd you say"
					], lower_transcription):
						app.speak(to_speak)
					else:
						app.speak("I'm sorry, that is not a valid response.")
		
except KeyboardInterrupt:
	print("Terminating application...")
	app.quit()
	print("Goodbye!")