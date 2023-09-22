from flask import Flask, request, jsonify, send_file
from flask_classful import FlaskView, route
from datetime import datetime

from AbstractAI.SpeechToText.WhisperSTT import WhisperSTT
from AbstractAI.Helpers.LogRequest import log_request

class STT_Server(FlaskView):
	def __init__(self, model_name):
		self.stt = WhisperSTT(model_name)
	
	def select_model(self, model_name:str) -> None:
		self.stt = WhisperSTT(model_name)
	
	def list_models(self):
		return WhisperSTT.list_models()
	
	@route('/transcribe', methods=['POST'])
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