from AbstractAI.Helpers.LLMStats import LLMStats
from datetime import datetime
from AbstractAI.Conversation import *

class LLM:
	def __init__(self):
		self.model_name = "Empty Model"
		self.stats = LLMStats()

	def start(self):
		print(f"\n\n\nLoading LLM \"{self.model_name}\"...\n\n\n")
	
	def raw_to_text(self, response) -> str:
		'''Pass a raw response from the model, get the text output from it.'''
		raise NotImplementedError
	
	def raw_output_token_count(self, response) -> str:
		'''Pass a raw response from the model, get the token count.'''
		raise NotImplementedError
		
	def prompt(self, prompt: str):
		'''Prompt the model and get a raw response. This is a blocking function.'''
		raise NotImplementedError
	
	def prompt_with_conversation(self, conversation: Conversation):
		prompt = self.generate_prompt(conversation)
		return self.prompt(prompt)
	
	def generate_prompt(self, conversation: Conversation) -> str:
		'''Generate a string prompt for the passed conversation in this LLM's preferred format.'''
		raise NotImplementedError
		
	def timed_prompt(self, prompt: str):
		'''Prompt the model with timing. This is a blocking function.'''
		start_time = datetime.now()
		output = self.prompt(prompt)
		generated_text = self.raw_to_text(output)
		end_time = datetime.now()
		
		print(f"Start time: {start_time}")
		print(f"End time: {end_time}")
		
		duration_seconds = (end_time - start_time).total_seconds()
		token_count = self.raw_output_token_count(output)
		char_count = len(generated_text)
		
		self.stats.duration.add(duration_seconds)
		self.stats.response_length.add(char_count)
		self.stats.token_count.add(token_count)
		self.stats.chars_per_second.add(char_count / duration_seconds)
		self.stats.tokens_per_second.add(token_count / duration_seconds)
		self.stats.print()
		return generated_text