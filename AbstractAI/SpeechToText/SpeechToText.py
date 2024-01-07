from abc import ABC, abstractmethod
from AbstractAI.SpeechToText.Logging.Model import ModelInfo

class SpeechToText(ABC):
	def __init__(self):
		self.info = ModelInfo()

	@abstractmethod
	def transcribe(self, file_name: str) -> dict:
		pass

	@abstractmethod
	def transcribe_str(self, file_name: str) -> str:
		pass
