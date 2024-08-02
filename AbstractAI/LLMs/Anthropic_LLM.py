from .LLM import *
from AbstractAI.Model.Settings.Anthropic_LLMSettings import Anthropic_LLMSettings
from anthropic import Anthropic
import json

class Anthropic_LLM(LLM):
	def __init__(self, settings: Anthropic_LLMSettings):
		self.client = None
		super().__init__(settings)
	
	def chat(self, conversation: Conversation, start_str: str = "", stream=False, max_tokens: int = None) -> LLM_Response | Iterator[LLM_Response]:
		wip_message, message_list = self._new_message(conversation, start_str, default_start_request_prompt)
		
		completion = self.client.messages.create(
			model=self.settings.model_name,
			max_tokens=max_tokens if max_tokens is not None else 1024,
			messages=message_list,
			stream=stream
		)
		
		if stream:
			response = LLM_Response(wip_message, completion.close)
			yield response
			
			for chunk in completion:
				if chunk.type == "message_start":
					response.input_token_count = chunk.message.usage.input_tokens
				elif chunk.type == "content_block_delta":
					response.message.append(chunk.delta.text)
					self._log_chunk(chunk.model_dump_json(indent=2), wip_message)
					response.source.out_token_count += 1
				elif chunk.type == "message_stop":
					response.source.finished = True
				yield response
			response.source.generating = False
		else:
			raise NotImplemented()
		return response
	
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