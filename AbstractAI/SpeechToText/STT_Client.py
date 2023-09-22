import requests
from AbstractAI.Helpers.Stopwatch import Stopwatch
from .STT import STT

class STT_Client(STT):
	def __init__(self, host: str, port: str):
		self.server_url = f"{host}:{port}"
	
	def list_models(self):
		return requests.get(f'{self.server_url}/list_models').json()['models']
	
	def select_model(self, model_name:str) -> None:
		requests.post(f'{self.server_url}/select_model', json={'model_name': model_name})
		
	def transcribe(self, file_name: str) -> dict:
		Stopwatch.singleton.start("Transcribing remotely")
		with open(file_name, 'rb') as audio_file:
			files = {'audio': audio_file}
			response = requests.post(f'{self.server_url}/transcribe', files=files)
			transcription = response.json()['transcription']
		self.last_transcription_time = Stopwatch.singleton.stop("Transcribing remotely")["last"]
		
		return {'text': transcription}
	
	def transcribe_str(self, file_name: str) -> str:
		return self.transcribe(file_name)['text']
