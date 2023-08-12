from .TextToSpeech import *
from io import BytesIO
import requests

class RemoteTTS:
	def __init__(self, host, port):
		self.host = host
		self.port = port

	def text_to_speech(self, text:str) -> AudioSegment:
		response = requests.post(f'{self.host}:{self.port}/tts', json={'text': text})
		audio_data = BytesIO(response.content)
		return AudioSegment.from_file(audio_data, format="wav")