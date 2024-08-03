from AbstractAI.LLMs.LLM import LLM
from AbstractAI.Model.Converse import Conversation, Message, Role
from AbstractAI.Model.Settings.Anthropic_LLMSettings import Anthropic_LLMSettings
from AbstractAI.Model.Converse.MessageSources import ModelSource
from anthropic import Anthropic
import json
from typing import List, Dict, Any

class Anthropic_LLM(LLM):
	def __init__(self, settings: Anthropic_LLMSettings):
		self.client = None
		super().__init__(settings)
	
	def chat(self, conversation: Conversation, start_str: str = "", stream: bool = False, max_tokens: int = None) -> Message:
		wip_message, message_list = self._new_message(conversation, start_str)
		
		completion = self.client.messages.create(
			model=self.settings.model_name,
			messages=message_list,
			max_tokens=max_tokens if max_tokens is not None else 1024,
			stream=stream
		)

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

	def conversation_to_list(self, conversation: Conversation) -> List[Dict[str,str]]:
		return super().conversation_to_list(conversation, False)