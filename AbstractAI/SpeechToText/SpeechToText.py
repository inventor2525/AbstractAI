from abc import ABC, abstractmethod
from AbstractAI.SpeechToText.Logging.Model import ModelInfo

class SpeechToText(ABC):
	def __init__(self):
		self.info = ModelInfo()
	
	@property
	def model_name(self) -> str:
		return self.info.name
	@model_name.setter
	def model_name(self, value: str):
		self.info.name = value
		self.info.new_id()
		
	@abstractmethod
	def transcribe(self, file_name: str) -> dict:
		pass

	@abstractmethod
	def transcribe_str(self, file_name: str) -> str:
		pass
