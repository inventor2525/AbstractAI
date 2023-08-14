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

def init_db():
	db_path = os.path.join(os.path.expanduser("~"), "ai_log.db")
	conn = sqlite3.connect(db_path)
	c = conn.cursor()
	c.execute('''CREATE TABLE IF NOT EXISTS llm_requests (text TEXT, prompt TEXT, response TEXT, tokens_in INT, tokens_out INT)''')
	c.execute('''CREATE TABLE IF NOT EXISTS transcriptions (file_name TEXT, transcription TEXT)''')
	c.execute('''CREATE TABLE IF NOT EXISTS tts_requests (text TEXT)''')
	conn.commit()
	conn.close()
	return db_path

def log_llm_request(text, prompt, response, tokens_in, tokens_out):
	conn = sqlite3.connect(DB_PATH)
	c = conn.cursor()
	c.execute("INSERT INTO llm_requests VALUES (?, ?, ?, ?, ?)", (text, prompt, response, tokens_in, tokens_out))
	conn.commit()
	conn.close()

def log_transcription(file_name, transcription):
	conn = sqlite3.connect(DB_PATH)
	c = conn.cursor()
	c.execute("INSERT INTO transcriptions VALUES (?, ?)", (file_name, transcription))
	conn.commit()
	conn.close()

def log_tts_request(text):
	conn = sqlite3.connect(DB_PATH)
	c = conn.cursor()
	c.execute("INSERT INTO tts_requests VALUES (?)", (text,))
	conn.commit()
	conn.close()
parser = argparse.ArgumentParser(description='Remote Speech-to-Text Server')
parser.add_argument('--model_name', type=str, choices=['tiny', 'tiny.en', 'small', 'small.en', 'medium', 'medium.en', 'large'], help='Whisper model size to use for transcription.', default='medium.en', required=False)
parser.add_argument('--llm_name', type=str, help='The LLM name to use.', default='stabilityai/StableBeluga-7B', required=False)
args = parser.parse_args()

app = Flask(__name__)

stt = WhisperSTT(args.model_name)

llm, prompt_generator = LoadLLM(args.llm_name, "You are a helpful AI.")
llm.start()

tts = MicrosoftSpeechT5_TTS()

# Initialize the database
DB_PATH = init_db()

@app.route('/transcribe', methods=['POST'])
def transcribe():
	audio_file = request.files['audio']
	ip_address = request.remote_addr.replace(".", "-")
	timestamp = datetime.now().strftime('%Y_%m_%d__%H_%M_%S')
	file_name = os.path.join(os.path.expanduser("~"), 'recordings', f'{ip_address}__{timestamp}.mp3')
	os.makedirs(os.path.dirname(file_name), exist_ok=True)
	audio_file.save(file_name)
	transcription = stt.transcribe_str(file_name)
	log_transcription(file_name, transcription)
	return jsonify({'transcription': transcription})

@app.route('/llm', methods=['POST'])
def llm_endpoint():	
	text = request.json['text']
	prompt_generator.add_prompt(text)
	
	prompt = prompt_generator.get_prompt()
	response = llm.timed_prompt( prompt )
	prompt_generator.add_response(response)
	
	log_llm_request(text, prompt, response, tokens_in, tokens_out)
	
	print(f"LLM was requested with this '{text}'\n\n(aka, '{prompt}')\n\nand returned '{response}'")
	return jsonify({'response': response})

@app.route('/tts', methods=['POST'])
def tts_endpoint():
	text = request.json['text']
	log_tts_request(text)
	audio_segment = tts.text_to_speech(text)
	buffer = BytesIO()
	audio_segment.export(buffer, format="mp3")
	buffer.seek(0)
	return send_file(buffer, mimetype="audio/mp3")

app.run(host='0.0.0.0', port=8000)
