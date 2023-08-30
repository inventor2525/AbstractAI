from .BaseMessageSource import BaseMessageSource, hash_property
from AbstractAI.Conversation.MessageSequence import MessageSequence
from typing import Dict

class ModelSource(BaseMessageSource):
	"""Describes a message from a Large Language Model."""

	def __init__(self, class_name: str, model_name: str, prompt: str, other_parameters: Dict = {}, message_sequence:"MessageSequence"=None, models_raw_output:str=None):
		super().__init__()
		self.class_name = class_name
		self.model_name = model_name
		self.other_parameters = other_parameters
		self.message_sequence = message_sequence
		self.models_raw_output = models_raw_output

	@hash_property
	def class_name(self, value: str):
		"""The python class name of the language model"""
		pass
		
	@hash_property
	def model_name(self, value: str):
		"""The model name string, eg: stabilityai/StableBeluga2 or gpt-3.5-turbo"""
		pass
		
	@hash_property
	def other_parameters(self, value: Dict):
		"""Additional parameters used by the model"""
		pass
		
	@hash_property
	def message_sequence(self, value: MessageSequence):
		"""The message sequence that was passed to the model in order to generate this message"""
		pass
	
	@hash_property
	def models_raw_output(self, value: dict):
		"""This is the json encoded raw output of the model, for OpenAI for instance it is the response from the chat completion. For Hugging face, it's the tokens as json."""
		pass