from abc import ABC, abstractmethod

class STT(ABC):
	def __init__(self):
		pass

	@abstractmethod
	def transcribe(self, file_name: str) -> dict:
		pass

	@abstractmethod
	def transcribe_str(self, file_name: str) -> str:
		pass
