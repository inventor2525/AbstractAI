from AbstractAI.ConversationModel import *
from AbstractAI.Helpers.LLMStats import LLMStats
from AbstractAI.LLMs.CommonRoles import CommonRoles
from AbstractAI.Helpers.JSONEncoder import JSONEncoder
from AbstractAI.Helpers.merge_dictionaries import *
from .LLM_Response import LLM_Response

from datetime import datetime
from abc import ABC, abstractmethod, abstractproperty
from typing import Any, Union, Dict, List
import json
	
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
		self.started = False

	def start(self):
		if self.started:
			return
		print(f"Loading LLM \"{self.model_info.model_name}\" using \"{self.model_info.class_name}\" with parameters: {json.dumps(self.model_info.parameters,indent=4, cls=JSONEncoder)}")
		self._load_model()
		print(f"LLM \"{self.model_info.model_name}\" loaded!")
		self.started = True
		
	def chat(self, conversation: Conversation, start_str:str="", stream=False, max_tokens:int=None) -> LLM_Response:
		'''
		Prompts the model with a Conversation and starts it's answer with
		start_str using a blocking method and creates a LLM_RawResponse
		from what it returns.
		'''
		chat = self.conversation_to_list(conversation)
		conversation_str = self._apply_chat_template(chat, start_str)
		wip_message = self._new_message(conversation_str, conversation, start_str)
		return self._complete_str_into(conversation_str, wip_message, stream, max_tokens)
		
	def complete_str(self, text:str, stream=False, max_tokens:int=None) -> LLM_Response:
		'''
		Similar to prompt, but allows passing raw strings to the model
		without any additional formatting being added.
		'''
		wip_message = self._new_message(text)
		return self._complete_str_into(text, wip_message, stream, max_tokens)
	
	@abstractmethod
	def _load_model(self):
		'''Load the model into memory.'''
		pass
	
	@abstractmethod
	def _complete_str_into(self, prompt: str, wip_message:Message, stream:bool=False, max_tokens:int=None) -> LLM_Response:
		'''
		Pass a string prompt to the model, and it will fill in wip_message.
		
		If stream is true, the message in LLM_RawResponse will start with a
		content = start_str, and the rest of the content will be streamed into
		it as you call next on the LLM_RawResponse. Changed notifications will
		come from the wip_message, so you can use it to update the UI or others.
		'''
		pass
	
	@abstractmethod
	def _apply_chat_template(self, chat: List[Dict[str,str]], start_str:str="") -> str:
		'''Generate a string prompt for the passed conversation in this LLM's preferred format.'''
		pass
	
	def conversation_to_list(self, conversation: Conversation) -> List[Dict[str,str]]:
		chat = []
		prev_role = None
		role_mapping = self.model_info.parameters["roles"]["mapping"]
		must_alternate = self.model_info.parameters["roles"]["must_alternate"]
		
		def append(msg:Dict[str,str], name:str):
			if name is not None:
				msg["name"] = name
			chat.append(msg)
		for message in conversation.message_sequence.messages:
			message_role, user_name = CommonRoles.from_source(message.source)
			role = role_mapping[message_role.value]
			if must_alternate:
				# Make sure roles alternate
				if prev_role is None and role == "assistant":
					append({
						"role":role_mapping[CommonRoles.User.value],
						"content":""
					}, user_name)
				if role == prev_role:
					chat[-1]["content"] += "\n\n" + message.content
				else:
					append({
						"role":role,
						"content":message.content
					}, user_name)
				prev_role = role
			else:
				append({
					"role":role,
					"content":message.content
				}, user_name)
		return chat
	
	def _serialize_raw_response(self, response:object) -> Dict[str,Any]:
		return response
		
	def _new_message(self, prompt: str, conversation:Conversation=None, start_str:str="") -> Message:
		'''Creates a new message that the model will fill in.'''
		message_sequence = None
		if conversation is not None:
			message_sequence = conversation.message_sequence
		
		# Store info about where the message came from:
		source = ModelSource(
			self.model_info, message_sequence=message_sequence,
			prompt=prompt, start_str=start_str
		)
		
		# Create the message object:
		return Message(start_str, source)
	
	def timed_prompt(self, model_input: Union[str, Conversation]) -> LLM_Response:
		'''
		Prompt the model with timing, can be either a string
		or a conversation. This is a blocking function.
		'''
		start_time = datetime.now()
		response:LLM_Response = None
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