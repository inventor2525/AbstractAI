import whisper
from AbstractAI.Helpers.Stopwatch import Stopwatch
import torch
from .STT import STT

class WhisperSTT(STT):
	def __init__(self, model_name: str):
		self.model_name = model_name

		# Load the Whisper model
		Stopwatch.singleton.start("Loading Whisper model")
		self.model = whisper.load_model(self.model_name)
		Stopwatch.singleton.stop("Loading Whisper model")
	
	def transcribe(self, file_name: str) -> dict:
		Stopwatch.singleton.start("Transcribing")
		result = self.model.transcribe(file_name, language="English", fp16=torch.cuda.is_available())
		self.last_transcription_time = Stopwatch.singleton.stop("Transcribing")["last"]
		
		return result
	
	def transcribe_str(self, file_name: str) -> str:
		return self.transcribe(file_name)['text']
