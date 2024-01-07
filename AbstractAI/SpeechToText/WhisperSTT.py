
import whisper
from AbstractAI.Helpers.Stopwatch import Stopwatch
import torch
from .SpeechToText import SpeechToText
from typing import List
from pydub import AudioSegment
import numpy as np

class WhisperSTT(SpeechToText):
	def __init__(self, model_name: str=None):
		super().__init__()
		self.model_name = model_name
		if self.model_name is not None:
			self.load_model(self.model_name)
	
	@property
	def model_name(self) -> str:
		return self.info.name
	@model_name.setter
	def model_name(self, value: str):
		self.info.name = value
	
	def load_model(self, model_name: str):
		self.model_name = model_name
		self.model = None

		# Load the Whisper model
		Stopwatch.singleton.start("Loading Whisper model", f" {self.model_name}")
		self.model = whisper.load_model(self.model_name)
		Stopwatch.singleton.stop("Loading Whisper model")
	
	def transcribe(self, audio:AudioSegment) -> dict:
		Stopwatch.singleton.start("Transcribing")

		# Convert to the expected format:
		if audio.frame_rate != 16000: # 16 kHz
			audio = audio.set_frame_rate(16000)
		if audio.sample_width != 2:   # int16
			audio = audio.set_sample_width(2)
		if audio.channels != 1:       # mono
			audio = audio.set_channels(1)
		audio_arr = np.array(audio.get_array_of_samples()).astype(np.float32)/32768.0

		result = self.model.transcribe(audio_arr, language='English', fp16=torch.cuda.is_available())
		self.last_transcription_time = Stopwatch.singleton.stop("Transcribing")["last"]
		
		return result
	
	def transcribe_str(self, audio:AudioSegment) -> str:
		return self.transcribe(audio)['text']
	
	@classmethod
	def list_models(cls) -> List[str]:
		return ["large", "medium", "small", "base", "tiny", "medium.en", "small.en", "base.en", "tiny.en"]