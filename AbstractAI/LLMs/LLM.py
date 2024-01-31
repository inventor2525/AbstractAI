from AbstractAI.ConversationModel import *
from AbstractAI.Helpers.LLMStats import LLMStats
from AbstractAI.LLMs.CommonRoles import CommonRoles
from AbstractAI.Helpers.JSONEncoder import JSONEncoder
from .LLM_RawResponse import LLM_RawResponse

from datetime import datetime
from abc import ABC, abstractmethod, abstractproperty
from typing import Any, Union, Dict, List
import json

def merge_dictionaries(dictionary1:dict, dictionary2:dict):
	open_list = [(dictionary1, dictionary2)]
	
	while len(open_list) > 0:
		dict1, dict2 = open_list.pop()
		
		for key, value in dict2.items():
			if key not in dict1:
				dict1[key] = value
			else:
				if isinstance(value, dict):
					if isinstance(dict1[key], dict):
						open_list.append((dict1[key], value))
					else:
						dict1[key] = value
				else:
					dict1[key] = value
	return dictionary1
	
class LLM(ABC):
	def __init__(self, model_name:str, parameters:Dict[str, Any]={}):
		default = {
			"roles": {
				"must_alternate": False,
				"mapping": {
					CommonRoles.System.value: "system",
					CommonRoles.User.value: "user",
					CommonRoles.Assistant.value: "assistant"
				}
			}
		}
		self.stats = LLMStats()
		self.model_info = ModelInfo(type(self).__name__, model_name, merge_dictionaries(default, parameters))

	def start(self):
		print(f"Loading LLM \"{self.model_info.model_name}\" using \"{self.model_info.class_name}\" with parameters: {json.dumps(self.model_info.parameters,indent=4, cls=JSONEncoder)}")
		self._load_model()
		print(f"LLM \"{self.model_info.model_name}\" loaded!")
		
	def chat(self, conversation: Conversation, start_str:str="") -> LLM_RawResponse:
		'''
		Prompts the model with a Conversation and starts it's answer with
		start_str using a blocking method and creates a LLM_RawResponse
		from what it returns.
		'''
		conversation_str = self._apply_chat_template(conversation, start_str)
		raw_response = self._complete_str(conversation_str)
		return self._create_response(conversation_str, raw_response, conversation, start_str)
		
	def complete_str(self, text:str) -> LLM_RawResponse:
		'''
		Similar to prompt, but allows passing raw strings to the model
		without any additional formatting being added.
		'''
		raw_response = self._complete_str(text)
		return self._create_response(text, raw_response)
	
	@abstractmethod
	def _load_model(self):
		'''Load the model into memory.'''
		pass
	
	@abstractmethod
	def _raw_to_text(self, response) -> str:
		'''Pass the raw output from the model, get the text output from it.'''
		pass
	
	@abstractmethod
	def _raw_output_token_count(self, response) -> Dict[str, int]:
		'''
		Pass a raw response from the model, get the token counts.
		
		Eg:
		{
		# 		"prompt_tokens": 164,
		# 		"completion_tokens": 121,
		# 		"total_tokens": 285
		# 	}
		'''
		pass
	
	@abstractmethod
	def _complete_str(self, prompt: str) -> object:
		'''
		Facilitates blocking prompts to the model,
		returning whatever the model does.
		'''
		pass
	
	@abstractmethod
	def _apply_chat_template(self, conversation: Conversation, start_str:str="") -> Any:
		'''Generate a string prompt for the passed conversation in this LLM's preferred format.'''
		pass
	
	def conversation_to_list(self, conversation: Conversation) -> List[Dict[str,str]]:
		chat = []
		prev_role = None
		role_mapping = self.model_info.parameters["roles"]["mapping"]
		must_alternate = self.model_info.parameters["roles"]["must_alternate"]
		for message in conversation.message_sequence.messages:
			message_role, user_name = CommonRoles.from_source(message.source)
			role = role_mapping[message_role.value]
			if must_alternate:
				# Make sure roles alternate
				if prev_role is None and role == "assistant":
					chat.append({
						"role":"user",
						"content":""
					})
				if role == prev_role:
					chat[-1]["content"] += "\n\n" + message.content
				else:
					chat.append({
						"role":role,
						"content":message.content
					})
				prev_role = role
			else:
				chat.append({
					"role":role,
					"content":message.content
				})
		return chat
	
	def _serialize_raw_response(self, response:object) -> Dict[str,Any]:
		return response
		
	def _create_response(self, prompt: str, raw_response:object, conversation:Conversation=None, start_str:str="") -> LLM_RawResponse:
		text_response = self._raw_to_text(raw_response)
		token_count = self._raw_output_token_count(raw_response)
		
		message_sequence = None
		if conversation is not None:
			message_sequence = conversation.message_sequence
		
		# Store info about where the message came from:
		source = ModelSource(
			self.model_info, message_sequence=message_sequence,
			prompt=prompt, start_str=start_str,
			serialized_raw_output=self._serialize_raw_response(raw_response)
		)
		
		# Create the message object:
		message = Message(start_str+text_response, source)
		
		return LLM_RawResponse(raw_response, message, token_count)
		
	def timed_prompt(self, model_input: Union[str, Conversation]) -> LLM_RawResponse:
		'''
		Prompt the model with timing, can be either a string
		or a conversation. This is a blocking function.
		'''
		start_time = datetime.now()
		response:LLM_RawResponse = None
		if isinstance(input, Conversation):
			response = self.chat(model_input)
		else:
			response = self.complete_str(model_input)
		end_time = datetime.now()
		
		print(f"Started prompting at: '{start_time}'\nFinished at: '{end_time}'")
		
		duration_seconds = (end_time - start_time).total_seconds()
		token_count = response.token_counts["completion_tokens"]
		char_count = len(response.message.content)
		
		self.stats.duration.add(duration_seconds)
		self.stats.character_count.add(char_count)
		self.stats.token_count.add(token_count)
		self.stats.chars_per_second.add(char_count / duration_seconds)
		self.stats.tokens_per_second.add(token_count / duration_seconds)
		self.stats.print()
		return response