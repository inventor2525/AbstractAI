from AbstractAI.Model.Converse import *
from AbstractAI.Helpers.merge_dictionaries import *
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
	
	def chat(self, conversation: Conversation, start_str:str="", stream=False, max_tokens:int=None) -> Message:
		'''
		Prompts the model with a Conversation and starts its answer with
		start_str using a blocking method and creates a Message from what it returns.
		'''
		raise NotImplementedError("This model's implementation does not support chat.")
	
	def _apply_chat_template(self, chat: List[Dict[str,str]], start_str:str="") -> str:
		'''Generate a string prompt for the passed conversation in this LLM's preferred format.'''
		raise NotImplementedError("This LLM does not expose it's chat format.")
	
	def count_tokens(self, text:str) -> int:
		'''Count the number of tokens in the passed text.'''
		raise NotImplementedError("This LLM does not support token counting.")
	
	def conversation_to_list(self, conversation: Conversation) -> List[Dict[str,str]]:
		role_mapping = {
			Role.System().type: self.settings.roles.System,
			Role.User().type: self.settings.roles.User,
			Role.Assistant().type: self.settings.roles.Assistant,
			Role.Tool().type: self.settings.roles.Tool
		}

		# Step 1: Convert conversation to list of dicts
		chat = []
		for message in conversation:
			role = role_mapping[message.role.type]
			msg_dict = {"role": role, "content": message.content}
			if self.settings.roles.include_names and message.role.name is not None:
				msg_dict["name"] = message.role.name
			chat.append(msg_dict)

		# Step 2: Change system messages to user messages if not accepted
		if not self.settings.roles.accepts_system_messages:
			for msg in chat:
				if msg["role"] == self.settings.roles.System:
					msg["role"] = self.settings.roles.User
					if self.settings.roles.include_names:
						msg["name"] = "system"

		# Step 3: Change mid-conversation system messages to user messages if not accepted
		elif not self.settings.roles.accepts_mid_conversation_system_messages:
			non_system_found = False
			for msg in chat:
				if msg["role"] != self.settings.roles.System:
					non_system_found = True
				elif non_system_found:
					msg["role"] = self.settings.roles.User
					if self.settings.roles.include_names:
						msg["name"] = "system"

		# Step 4: Merge consecutive messages
		if self.settings.roles.merge_consecutive_messages_by_same_role:
			merged_chat = []
			for msg in chat:
				if merged_chat and (merged_chat[-1]["role"], merged_chat[-1].get("name", None)) == (msg["role"], msg.get("name", None)):
					merged_chat[-1]["content"] += f"\n\n{msg['content']}"
				else:
					merged_chat.append(msg.copy())
			chat = merged_chat

		# Step 5: Ensure alternating messages if required
		if self.settings.roles.must_alternate:
			alternating_chat = []
			prev_relevant_role = self.settings.roles.Assistant
			for msg in chat:
				if msg["role"] in [self.settings.roles.User, self.settings.roles.Assistant]:
					if msg["role"] == prev_relevant_role:
						opposite_role = self.settings.roles.User if msg["role"] == self.settings.roles.Assistant else self.settings.roles.Assistant
						alternating_chat.append({"role": opposite_role, "content": ""})
					alternating_chat.append(msg)
					prev_relevant_role = msg["role"]
				else:
					alternating_chat.append(msg)
			
			chat = alternating_chat

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
				if message_list[-1]["role"] != "user":
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
		model_source = message.get_source(ModelSource)
		if "Chunks" not in model_source.serialized_raw_output:
			model_source.serialized_raw_output["Chunks"] = []
		model_source.serialized_raw_output["Chunks"].append(chunk)
	
	def _dict_from_obj(self, obj):
		'''
		Helper method that converts a object based
		return from many api's into a dictionary.
		'''
		if hasattr(obj, "__dict__"):
			return {k: self._dict_from_obj(v) for k, v in obj.__dict__.items() if not k.startswith("_")}
		elif isinstance(obj, (list, tuple)):
			return [self._dict_from_obj(item) for item in obj]
		elif isinstance(obj, dict):
			return {k: self._dict_from_obj(v) for k, v in obj.items()}
		else:
			return obj