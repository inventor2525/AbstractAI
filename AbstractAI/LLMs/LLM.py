from AbstractAI.Helpers.LLMStats import LLMStats
from datetime import datetime
from AbstractAI.ConversationModel import *
from abc import ABC, abstractmethod, abstractproperty
from .LLM_RawResponse import LLM_RawResponse
from typing import Union, Dict
import json

class LLM(ABC):
	def __init__(self, model_name:str="Empty Model"):
		self.model_name = model_name
		self.stats = LLMStats()

	def start(self):
		print(f"\n\n\nLoading LLM \"{self.model_name}\"...\n\n\n")
	
	@abstractmethod
	def _raw_to_text(self, response) -> str:
		'''Pass a raw response from the model, get the text output from it.'''
		pass
	
	@abstractmethod
	def _raw_output_token_count(self, response) -> int:
		'''Pass a raw response from the model, get the token count.'''
		pass
	
	@abstractmethod
	def _prompt_str(self, prompt: str) -> object:
		'''
		Facilitates blocking prompts to the model,
		returning whatever the model does.
		'''
		pass
	
	@abstractmethod
	def generate_prompt_str(self, conversation: Conversation) -> str:
		'''Generate a string prompt for the passed conversation in this LLM's preferred format.'''
		pass
	
	@property
	def other_parameters(self) -> Dict:
		op = getattr(self, "_other_parameters", None)
		if op is None:
			self._other_parameters = {}
			return self._other_parameters
		return op
		
	@other_parameters.setter
	def other_parameters(self, value):
		self._other_parameters = value
	
	def _serialize_raw_response(self, response:object) -> str:
		return response
		
	def _create_response(self, prompt: str, raw_response:object, conversation:Conversation=None) -> LLM_RawResponse:
		text_response = self._raw_to_text(raw_response)
		token_count = self._raw_output_token_count(raw_response)
		
		message_sequence = None
		if conversation is not None:
			message_sequence = conversation.message_sequence
		
		# Store info about where the message came from:
		source = ModelSource(
			type(self).__name__, self.model_name, 
			self.other_parameters, message_sequence=message_sequence,
			prompt=prompt,
			models_serialized_raw_output=self._serialize_raw_response(raw_response)
		)
		
		# Create the message object:
		message = Message(text_response, source)
		
		return LLM_RawResponse(raw_response, message, token_count)
		
	def prompt(self, conversation: Conversation) -> LLM_RawResponse:
		'''
		Prompts the model with a Conversation using a blocking method
		and creates a LLM_RawResponse from what it returns.
		'''
		prompt_string = self.generate_prompt_str(conversation)
		raw_response = self._prompt_str(prompt_string)
		return self._create_response(prompt_string, raw_response, conversation)
		
	def prompt_str(self, prompt_string:str) -> LLM_RawResponse:
		'''
		Similar to prompt, but allows passing raw strings to the model
		without any additional formatting being added.
		'''
		raw_response = self._prompt_str(prompt_string)
		return self._create_response(prompt_string, raw_response)
		
	def timed_prompt(self, model_input: Union[str, Conversation]) -> LLM_RawResponse:
		'''
		Prompt the model with timing, can be either a string
		or a conversation. This is a blocking function.
		'''
		start_time = datetime.now()
		response:LLM_RawResponse = None
		if isinstance(input, Conversation):
			response = self.prompt(model_input)
		else:
			response = self.prompt_str(model_input)
		end_time = datetime.now()
		
		print(f"Started prompting at: '{start_time}'\nFinished at: '{end_time}'")
		
		duration_seconds = (end_time - start_time).total_seconds()
		token_count = response.token_count
		char_count = len(response.message.content)
		
		self.stats.duration.add(duration_seconds)
		self.stats.character_count.add(char_count)
		self.stats.token_count.add(token_count)
		self.stats.chars_per_second.add(char_count / duration_seconds)
		self.stats.tokens_per_second.add(token_count / duration_seconds)
		self.stats.print()
		return response