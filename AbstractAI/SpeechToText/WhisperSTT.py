
import whisper
from AbstractAI.Helpers.Stopwatch import Stopwatch
import torch
from .STT import STT
from ClassyFlaskDB.Flaskify import Route, Flaskify
from typing import List
from pydub import AudioSegment

import os
from datetime import datetime

@Flaskify()
class WhisperSTT(STT):
	def __init__(self, model_name: str=None):
		self.model_name = model_name
		if self.model_name is not None:
			self.load_model(self.model_name)
	
	def load_model(self, model_name: str):
		self.model_name = model_name
		self.model = None

		# Load the Whisper model
		Stopwatch.singleton.start("Loading Whisper model", f" {self.model_name}")
		self.model = whisper.load_model(self.model_name)
		Stopwatch.singleton.stop("Loading Whisper model")
	
	def transcribe(self, file_name: str) -> dict:
		Stopwatch.singleton.start("Transcribing")
		result = self.model.transcribe(file_name, language="English", fp16=torch.cuda.is_available())
		self.last_transcription_time = Stopwatch.singleton.stop("Transcribing")["last"]
		
		return result
	
	def transcribe_str(self, file_name: str) -> str:
		return self.transcribe(file_name)['text']
	
	@staticmethod
	def singleton() -> 'WhisperSTT':
		if not hasattr(WhisperSTT, "_singleton"):
			WhisperSTT._singleton = WhisperSTT()
		return WhisperSTT._singleton
	
	@Route()
	@staticmethod
	def list_models() -> List[str]:
		return ["large", "medium", "small", "base", "tiny", "large.en", "medium.en", "small.en", "base.en", "tiny.en"]
	
	@Route()
	@staticmethod
	def load_model(model_name: str):
		WhisperSTT.singleton().load_model(model_name)

	@Route()
	@staticmethod
	def transcribe(audio:AudioSegment) -> dict:
		timestamp = datetime.now().strftime('%Y_%m_%d__%H_%M_%S')
		file_name = os.path.join(os.path.expanduser("~"), 'recordings', f'{ip_address}__{timestamp}.mp3')
		os.makedirs(os.path.dirname(file_name), exist_ok=True)
		
		audio.save(file_name)
		return WhisperSTT.singleton().transcribe_str(file_name)
	
	@Route()
	@staticmethod
	def transcribe_str(file_name: str) -> str:
		return WhisperSTT.singleton().transcribe_str(file_name)