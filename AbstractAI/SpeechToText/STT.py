import whisper
from AbstractAI.Helpers.Stopwatch import Stopwatch
import torch

class STT():
	def __init__(self, model_name:str):
		'''model_name: "tiny", "small", "medium", "large"'''
		self.model_name = model_name

		# Load the Whisper model
		Stopwatch.singleton.start("Loading Whisper model")
		self.model = whisper.load_model(model_size)
		Stopwatch.singleton.stop("Loading Whisper model")
	
	def transcribe(self, file_name:str) -> dict:
		'''Transcribe the audio data at file_name with Whisper.'''
		Stopwatch.singleton.start("Transcribing")
		result = self.model.transcribe(file_name, language="English", fp16=torch.cuda.is_available())
		tt = Stopwatch.singleton.stop("Transcribing")["last"]
		
		print(f"Transcribed at {rt/tt} seconds per second")
		return result
	
	def transcribe_str(self, file_name:str) -> str:
		return self.transcribe(file_name)['text']