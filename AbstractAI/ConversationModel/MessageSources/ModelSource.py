from .MessageSource import MessageSource
from AbstractAI.ConversationModel.ModelBase import *
from AbstractAI.ConversationModel.MessageSequence import MessageSequence
from typing import Dict

@DATA
class ModelSource(MessageSource):
	'''Describes a message from a Large Language Model.'''
	class_name: str
	model_name: str
	model_parameters: dict = field(default_factory=dict)
	message_sequence: MessageSequence = None
	prompt: str = None

	models_serialized_raw_output: str = None