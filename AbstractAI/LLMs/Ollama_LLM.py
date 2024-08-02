from AbstractAI.LLMs.LLM import *
from AbstractAI.Model.Settings.Ollama_LLMSettings import Ollama_LLMSettings
import ollama

class Ollama_LLM(LLM):
	def __init__(self, settings:Ollama_LLMSettings):
		self.client = None
		super().__init__(settings)
	
	def chat(self, conversation: Conversation, start_str:str="", stream=False, max_tokens:int=None) -> Union[LLM_Response, Iterator[LLM_Response]]:
		wip_message, message_list = self._new_message(conversation, start_str, default_start_request_prompt)
		
		completion = ollama.chat(
			model=self.settings.model_name,
			messages=message_list,
			stream=stream
		)
		
		if stream:
			response = LLM_Response(wip_message, completion.close)
			yield response
			
			for i, chunk in enumerate(completion):
				if i > max_tokens-1:
					response.stop()
					break
				if response.message.append(chunk['message']['content']):
					response.source.out_token_count += 1
				self._log_chunk(chunk, wip_message)
				response.source.finished = chunk.get('done_reason', None) == 'stop'
				yield response
			response.source.generating = False
		else:
			response.source.finished = completion['done_reason'] == 'stop'
			response.message.content = completion['message']['content']
			response.source.out_token_count = completion['eval_count']
			response.source.serialized_raw_output = completion
			response.source.generating = False
		
		return response