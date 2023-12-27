
from .SpeechToText import SpeechToText
from AbstractAI.Remote.client import System
from pydub import AudioSegment

class RemoteSTT(SpeechToText):
	def __init__(self, model_name: str=None):
		self.model_name = model_name
		if self.model_name is not None:
			self.load_model(self.model_name)
	
	def transcribe(self, audio:AudioSegment) -> dict:
		return System.transcribe(audio)
	
	def transcribe_str(self, audio:AudioSegment) -> str:
		return System.transcribe_str(audio)