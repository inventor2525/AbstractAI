from .LLM import *
import tiktoken
import openai
import json
import os

class OpenAI_LLM(LLM):
	def __init__(self, model_name="gpt-3.5-turbo", temperature=0):
		super().__init__(model_name)
		openai.api_key_path = os.path.expanduser("~/.config/ModelProgrammer/API_key.txt")
		
		self.temperature = temperature
		self.encoding = tiktoken.encoding_for_model(self.model_name)
	
	def _raw_to_text(self, response) -> str:
		return response["choices"][0]["message"]["content"]
	
	def _raw_output_token_count(self, response) -> int:
		response_text = self._raw_to_text(response)
		response_tokens = self.encoding.encode(response_text)
		return len(response_tokens)
	
	def _prompt_str(self, prompt):
		raise Exception("This doesn't support string prompts")
	
	def prompt(self, conversation: Conversation) -> LLM_RawResponse:
		'''
		Prompts the model with a Conversation using a blocking method
		and creates a LLM_RawResponse from what it returns.
		'''
		message_list = []
		for message in conversation.message_sequence.messages:
			message_dict = {
				"role": "assistant" if message.role == Role.Assistant else "user",
				"content":message.content
			}
			if message.role != Role.Assistant and message.role != Role.User:
				message_dict["name"] = str(message.role).lower()
			message_list.append(message_dict)
		
		raw_response = openai.ChatCompletion.create(
			model=self.model,
			messages=message_list,
			temperature=self.temperature,
			max_tokens=max_tokens,
		)
		
		self.other_parameters = {
			"temperature":self.temperature,
			"max_tokens":max_tokens
		}
		return self._create_response(json.dumps(message_list), raw_response, conversation)