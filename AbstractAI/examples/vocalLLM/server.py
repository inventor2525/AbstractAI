import os
import sqlite3
from datetime import datetime
import argparse
from flask import Flask, request, jsonify, send_file
from AbstractAI.SpeechToText.WhisperSTT import WhisperSTT
from AbstractAI.TextToSpeech.MicrosoftSpeechT5_TTS import MicrosoftSpeechT5_TTS
from AbstractAI.LLMs.LoadLLM import *
from pydub import AudioSegment
from io import BytesIO
import re
from AbstractAI.ChatBot import *
from AbstractAI.DB.Database import *

def init_db(model_name, llm_name):
	db_path = os.path.join(os.path.expanduser("~"), "ai_log.db")
	conn = sqlite3.connect(db_path)
	c = conn.cursor()
	c.execute('''CREATE TABLE IF NOT EXISTS llm_requests (date_time TEXT, ip TEXT, text TEXT, prompt TEXT, response TEXT, tokens_in INT, tokens_out INT)''')
	c.execute('''CREATE TABLE IF NOT EXISTS transcriptions (date_time TEXT, ip TEXT, file_name TEXT, transcription TEXT)''')
	c.execute('''CREATE TABLE IF NOT EXISTS tts_requests (date_time TEXT, ip TEXT, text TEXT)''')
	c.execute('''CREATE TABLE IF NOT EXISTS sessions (version TEXT, date_time TEXT, model_name TEXT, llm_name TEXT)''')
	c.execute("INSERT INTO sessions VALUES (?, ?, ?, ?)", ("1.0.0", datetime.now().strftime('%Y-%m-%d %H:%M:%S'), model_name, llm_name))
	conn.commit()
	conn.close()
	return db_path

def log_request(table, ip, values):
	conn = sqlite3.connect(DB_PATH)
	c = conn.cursor()
	c.execute(f"INSERT INTO {table} VALUES (?, ?, {', '.join(['?']*len(values))})", (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), ip, *values))
	conn.commit()
	conn.close()

parser = argparse.ArgumentParser(description='Remote Speech-to-Text Server')
parser.add_argument('--model_name', type=str, choices=['tiny', 'tiny.en', 'small', 'small.en', 'medium', 'medium.en', 'large'], help='Whisper model size to use for transcription.', default='medium.en', required=False)
parser.add_argument('--llm_name', type=str, help='The LLM name to use.', default='stabilityai/StableBeluga-7B', required=False)
args = parser.parse_args()

app = Flask(__name__)

stt = WhisperSTT(args.model_name)

conversation = Conversation()
conversation.add_message(Message("You are a helpful AI.", Role.System, UserSource("System")))
llm = LoadLLM(args.llm_name)

bot = ChatBot(llm, Database("sqlite:///chatbot.sql"), conversation)

tts = MicrosoftSpeechT5_TTS()

# Initialize the database
DB_PATH = init_db(args.model_name, args.llm_name)

@app.route('/transcribe', methods=['POST'])
def transcribe():
	audio_file = request.files['audio']
	ip_address = request.remote_addr.replace(".", "-")
	timestamp = datetime.now().strftime('%Y_%m_%d__%H_%M_%S')
	file_name = os.path.join(os.path.expanduser("~"), 'recordings', f'{ip_address}__{timestamp}.mp3')
	os.makedirs(os.path.dirname(file_name), exist_ok=True)
	
	audio_file.save(file_name)
	transcription = stt.transcribe_str(file_name)
	
	log_request("transcriptions", request.remote_addr, (file_name, transcription))
	return jsonify({'transcription': transcription})

@app.route('/llm', methods=['POST'])
def llm_endpoint():
	text = request.json['text']
	response = bot.prompt(prompt=text)
	prompt = text
	log_request("llm_requests", request.remote_addr, (text, prompt, response, None, None))
	print(f"LLM was requested with this '{text}'\n\n(aka, '{prompt}')\n\nand returned '{response}'")
	return jsonify({'response': response})

def split_codeblocks(text):
	'''Separates out the code blocks from input text.'''
	pattern = r'```^(\w+)?$'
	inside_code_block = False
	delimiter_count = 0
	regular_text = ''
	code_blocks = []
	code_block_content = ''
	for line in text.split('\n'):
		match = re.match(pattern, line)
		if match:
			if match.group(1):  # Start of a code block
				delimiter_count += 1
				inside_code_block = True
				language = match.group(1) if match.group(1) else ''
			else:  # End of a code block
				delimiter_count -= 1
				if delimiter_count == 0:
					inside_code_block = False
					code_blocks.append(code_block_content.strip())
					regular_text += 'Some ' + language + ' code\n'
					code_block_content = ''
		if inside_code_block:
			code_block_content += line + '\n'
		else:
			regular_text += line + '\n'
	return regular_text, code_blocks
	
@app.route('/tts', methods=['POST'])
def tts_endpoint():
	text = request.json['text']
	log_request("tts_requests", request.remote_addr, (text,))
	
	separated_text,_ = split_codeblocks(text)
	audio_segment = tts.text_to_speech(separated_text)
	
	buffer = BytesIO()
	audio_segment.export(buffer, format="mp3")
	buffer.seek(0)
	return send_file(buffer, mimetype="audio/mp3")

app.run(host='0.0.0.0', port=8000)
