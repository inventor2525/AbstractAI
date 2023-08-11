import argparse
from flask import Flask, request, jsonify
from AbstractAI.SpeechToText.WhisperSTT import WhisperSTT
from AbstractAI.LLMs.LoadLLM import *

parser = argparse.ArgumentParser(description='Remote Speech-to-Text Server')
parser.add_argument('--model_name', type=str, choices=['tiny', 'tiny.en', 'small', 'small.en', 'medium', 'medium.en', 'large'], help='Whisper model size to use for transcription.', default='medium.en', required=False)
parser.add_argument('--llm_name', type=str, help='The LLM name to use.', default='stabilityai/StableBeluga2-7B', required=False)
args = parser.parse_args()

app = Flask(__name__)
stt = WhisperSTT(args.model_name)
llm, prompt_generator = LoadLLM(args.llm_name, "You are a helpful AI.")
llm.start()

@app.route('/transcribe', methods=['POST'])
def transcribe():
	audio_file = request.files['audio']
	file_name = 'received.wav'
	audio_file.save(file_name)
	transcription = stt.transcribe_str(file_name)
	return jsonify({'transcription': transcription})

@app.route('/llm', methods=['POST'])
def llm_endpoint():
	prompt_generator.reset()
	
	text = request.json['text']
	prompt_generator.add_prompt(text)
	response = llm.timed_prompt(prompt_generator.get_prompt())
	prompt_generator.add_response(response)
	print(f"LLM was requested with this {text} and returned {response}")
	return jsonify({'response': response})

app.run(host='0.0.0.0', port=8000)
