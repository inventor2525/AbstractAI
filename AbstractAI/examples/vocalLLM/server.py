import argparse
from flask import Flask, request, jsonify
from AbstractAI.SpeechToText.WhisperSTT import WhisperSTT
from AbstractAI.LLMs.LoadLLM import LoadLLM

parser = argparse.ArgumentParser(description='Remote Speech-to-Text Server')
parser.add_argument('model_name', type=str, choices=['tiny', 'tiny.en', 'small', 'small.en', 'medium', 'medium.en', 'large'], help='Whisper model size to use for transcription.')
parser.add_argument('llm_name', type=str, help='The LLM name to use.', default='stabilityai/StableBeluga2-7B')
args = parser.parse_args()

app = Flask(__name__)
stt = WhisperSTT(args.model_name)
llm, _ = LoadLLM(args.llm_name, "You are a helpful AI.")

@app.route('/transcribe', methods=['POST'])
def transcribe():
	audio_file = request.files['audio']
	file_name = 'received.wav'
	audio_file.save(file_name)
	transcription = stt.transcribe_str(file_name)
	return jsonify({'transcription': transcription})

@app.route('/llm', methods=['POST'])
def llm_endpoint():
	text = request.json['text']
	response = llm.timed_prompt(text)
	print(f"LLM was requested with this {text} and returned {response}")
	return jsonify({'response': response})

app.run(host='0.0.0.0', port=8000)
