from AbstractAI.LLMs.LLM import Conversation, Iterator, LLM_Response, Union
from AbstractAI.LLMs.OpenAI_LLM import *
from groq import Groq

class Groq_LLM(OpenAI_LLM):
	def _load_model(self):
		self.client = Groq(api_key=self.settings.api_key)
	
	def chat(self, conversation: Conversation, start_str: str = "", stream=False, max_tokens: int = None, auto_append: bool = False) -> LLM_Response | Iterator[LLM_Response]:
		print(f"Starting chat for conversation: {conversation.get_primary_key()}")
		ret = super().chat(conversation, start_str, stream, max_tokens, auto_append)
		if stream:
			for r in ret:
				print(f"Received stream chunk: {r.message.content[:50]}...")
				try:
					response_chunks = r.source.serialized_raw_output["Chunks"]
					usage = response_chunks[-1]["x_groq"]["usage"]
					r.source.in_token_count = usage.get("prompt_tokens",r.source.in_token_count)
					total_tokens = usage.get("total_tokens",-1)
					if total_tokens>-1:
						r.source.out_token_count = total_tokens - r.source.in_token_count
				except:
					pass
				
				yield r
		else:
			print(f"Received full response: {ret.message.content[:50]}...")
			return ret