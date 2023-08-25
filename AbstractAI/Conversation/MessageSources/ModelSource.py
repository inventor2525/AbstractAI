from . import BaseMessageSource, hash_property
from typing import Dict

class ModelSource(BaseMessageSource):
	"""Describes a message from a Large Language Model."""

	def __init__(self, class_name: str, model_name: str, prompt: str, other_parameters: Dict = {}, message_sequence:"MessageSequence"=None):
		super().__init__()
		# The python class name of the language model
		self.class_name: str = class_name
		
		# The model name string, eg: stabilityai/StableBeluga2 or gpt-3.5-turbo
		self.model_name: str = model_name
		
		# Additional parameters used by the model
		self.other_parameters: Dict = other_parameters
		
		# The message sequence that was passed to the model in order to generate this message
		self.message_sequence = message_sequence
		
	def recompute_hash(self):
		self._hash = self._compute_hash((self.class_name, self.model_name, self.other_parameters, self.message_sequence.hash))