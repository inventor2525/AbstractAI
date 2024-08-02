from AbstractAI.Model.Converse import *
from AbstractAI.Helpers.merge_dictionaries import *
from .LLM_Response import LLM_Response
from AbstractAI.Conversable import Conversable

from datetime import datetime
from typing import Any, Union, Dict, List, Iterator, Tuple, Optional
import json

from AbstractAI.Helpers.func_to_model import kwargs_from_instance
from AbstractAI.Model.Settings.LLMSettings import LLMSettings

default_start_request_prompt = r"""Please begin your response with:<|start_str|>"""

class LLM(Conversable):
	def __init__(self, settings:LLMSettings):
		self.settings = settings
		self.started = False

	def start(self):
		if self.started:
			return
		print(f"Loading LLM \"{self.settings.user_model_name}\" using \"{type(self).__name__}\"")
		self._load_model()
		print(f"LLM \"{self.settings.user_model_name}\" loaded!")
		self.started = True
	
	def _load_model(self):
		'''Load the model into memory.'''
		pass
	
	def chat(self, conversation: Conversation, start_str:str="", stream=False, max_tokens:int=None) -> Union[LLM_Response, Iterator[LLM_Response]]:
		'''
		Prompts the model with a Conversation and starts it's answer with
		start_str using a blocking method and creates a LLM_RawResponse
		from what it returns.
		'''
		raise NotImplementedError("This model's implementation does not support chat.")
	
	def complete_str(self, text:str, stream=False, max_tokens:int=None) -> Union[LLM_Response, Iterator[LLM_Response]]:
		'''
		Similar to prompt, but allows passing raw strings to the model
		without any additional formatting being added.
		'''
		raise NotImplementedError("This model's implementation does not support simple text completion.")
	
	def _apply_chat_template(self, chat: List[Dict[str,str]], start_str:str="") -> str:
		'''Generate a string prompt for the passed conversation in this LLM's preferred format.'''
		raise NotImplementedError("This LLM does not expose it's chat format.")
	
	def count_tokens(self, text:str) -> int:
		'''Count the number of tokens in the passed text.'''
		raise NotImplementedError("This LLM does not support token counting.")
	
	def conversation_to_list(self, conversation: Conversation, include_names:bool=True) -> List[Dict[str,str]]:
		chat = []
		prev_role:Role = None
		role_mapping  = {
			Role.System().type: self.settings.roles.System,
			Role.User().type: self.settings.roles.User,
			Role.Assistant().type: self.settings.roles.Assistant
		}
		should_merge = self.settings.roles.merge_consecutive_messages_by_same_role
		
		def append_msg(message:Message, role:Role):
			m = {
				"role":role_mapping[role.type],
				"content":message.content
			}
			if role.name is not None and include_names:
				m["name"] = role.name
			chat.append(m)
		def append_empty(role:str):
			chat.append({"role":role, "content":""})
			
		for message in conversation.message_sequence.messages:
			role:Role = message.role
			if not self.settings.roles.accepts_system_messages:
				if role.type == System.type:
					role = Role.User()
			
			if self.settings.roles.must_alternate:
				# Make sure roles alternate
				if prev_role is None and role.type == Role.Assistant().type:
					append_empty(Role.User().type)
				
				if role.type == prev_role.type:
					if should_merge and role == prev_role: #names might not be ==
						chat[-1]["content"] += "\n\n" + message.content
					else:
						if role.type == Role.Assistant().type:
							append_empty(User.type)
						else:
							append_empty(Role.Assistant().type)
						append_msg(message, role)
				else:
					append_msg(message, role)
			else:
				if role == prev_role and (not include_names or user_name == prev_user_name):
					chat[-1]["content"] += "\n\n" + message.content
				else:
					append_msg(message, role)
			prev_role = role
		return chat
		
	def _new_message(self, input:Union[str,Conversation]=None, start_str:str="", start_request_prompt:str=None) -> Tuple[Message, Optional[List[Dict[str,str]]]]:
		'''
		Creates a new message that the model will fill in.
		
		Optionally pass start_str to begin the models response with that.
		
		If a model's api does not support start_str's, you can pass start_request_prompt
		to 'ask' it to start it's response with start_str using a custom prompt where
		"<|start_str|>" will be replaced with start_str. If start_request_prompt is left
		None then it is assumed your model can handle start_str and it will be stored in
		the source information as normal. - Note that this method WILL cost you input tokens.
		'''
		source = ModelSource(settings=self.settings, start_str=start_str) | CallerInfo.catch([1,2])
		source.generating = True
		message_list = None
		new_message = Message("", Role.Assistant()) | source
		
		if isinstance(input, Conversation):
			source.message_sequence = input.message_sequence
			message_list = self.conversation_to_list(input)
			
			if start_request_prompt and start_str and len(start_str)>0:
				start_request_prompt = start_request_prompt.replace("<|start_str|>", start_str)
				if message_list[-1]["role"] is not "user":
					message_list.append({"role":"user", "content":start_request_prompt})
				else:
					message_list[-1]["content"] = f"{message_list[-1]['content']}\n\n{start_request_prompt}"
			try:
				source.prompt = self._apply_chat_template(message_list, start_str)
				source.in_token_count = self.count_tokens(source.prompt)
			except:
				if source.prompt is None:
					source.prompt = json.dumps(message_list, indent=4)
				
		elif isinstance(input, str):
			source.prompt = input
			try:
				source.in_token_count = self.count_tokens(input)
			except:
				pass
		else:
			raise ValueError("Invalid input type. 'Input' should be a Conversation or a string.")
			
		return new_message, message_list
	
	def _log_chunk(self, chunk:Dict[str,Any], message:Message):
		if "Chunks" not in message.source.serialized_raw_output:
			message.source.serialized_raw_output["Chunks"] = []
		message.source.serialized_raw_output["Chunks"].append(chunk)