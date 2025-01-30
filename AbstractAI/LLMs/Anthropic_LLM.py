from AbstractAI.LLMs.LLM import LLM
from AbstractAI.Model.Converse import Conversation, Message, Role
from AbstractAI.Model.Settings.Anthropic_LLMSettings import Anthropic_LLMSettings
from AbstractAI.Model.Converse.MessageSources import ModelSource
from anthropic import Anthropic
import json
from typing import List, Dict, Any
from anthropic import NOT_GIVEN

class Anthropic_LLM(LLM):
	def __init__(self, settings: Anthropic_LLMSettings):
		self.client = None
		super().__init__(settings)
		self._prev_cached_msg = None
	
	def chat(self, conversation: Conversation, start_str: str = "", stream: bool = False, max_tokens: int = None) -> Message:
		wip_message, message_list = self._new_message(conversation, start_str)
		
		def make_msg_cached(msg:Dict[str, str]):
			msg['content'] = [{
				'type':'text',
				'text':msg['content'],
				"cache_control": {"type": "ephemeral"}
			}]
		
		if self.settings.rolling_cache:
			if self._prev_cached_msg: #The simple egotist implementation (there is only *1* conversation in the app, more will break this, but it doesn't matter cause there should only ever be 1 conversation. GOT IT?!?! Good!)
				for msg in reversed(message_list):
					if msg['content'] == self._prev_cached_msg:
						make_msg_cached(msg)
			if len(message_list)>0:
				self._prev_cached_msg = message_list[-1]['content']
				make_msg_cached(message_list[-1])
		
		system_message = NOT_GIVEN
		if len(message_list)>0 and message_list[0]['role'] == 'system':
			system_message = message_list[0]['content']
			message_list = message_list[1:]
		
		for msg in message_list:
			if msg['role'] == 'system':
				msg['role'] = 'user'
		
		try:
			completion = self.client.messages.create(
				model=self.settings.model_name,
				system=system_message,
				messages=message_list,
				max_tokens=max_tokens if max_tokens is not None else 1024,
				stream=stream
			)
			print(completion)
		except Exception as e:
			print(e)
		if stream:
			chunk_iterator = iter(completion)

			def continue_function():
				try:
					chunk = next(chunk_iterator)
					if chunk.type == "message_start":
						wip_message.source.in_token_count = chunk.message.usage.input_tokens
					elif chunk.type == "content_block_delta":
						if wip_message.append(chunk.delta.text):
							wip_message.source.out_token_count += 1
					elif chunk.type == "message_stop":
						wip_message.source.finished = True
					self._log_chunk(self._dict_from_obj(chunk), wip_message)
					return True
				except StopIteration:
					wip_message.source.generating = False
					wip_message.source.finished = True
					return False

			wip_message.source.continue_function = continue_function
			wip_message.source.stop_function = completion.close
		else:
			wip_message.content = completion.content[0].text
			wip_message.source.finished = True
			wip_message.source.serialized_raw_output = self._dict_from_obj(completion)
			
			wip_message.source.in_token_count = completion.usage.input_tokens
			wip_message.source.out_token_count = completion.usage.output_tokens

			wip_message.source.generating = False

		return wip_message

	def _apply_chat_template(self, chat: List[Dict[str, str]], start_str: str = "") -> str:
		if start_str is not None and len(start_str) > 0:
			raise Exception("Start string not supported by Anthropic")
		return json.dumps(chat)
	
	def _load_model(self):
		self.client = Anthropic(api_key=self.settings.api_key)
	
	def count_tokens(self, text: str) -> int:
		return self.client.count_tokens(text)