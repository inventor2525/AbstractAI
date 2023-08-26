from AbstractAI.Helpers.AMMS import AMMS

class LLMStats:
	def __init__(self):
		self.duration = AMMS()
		self.character_count = AMMS()
		self.token_count = AMMS()
		self.chars_per_second = AMMS()
		self.tokens_per_second = AMMS()
		
	def print(self):
		print(f"Duration: {self.duration}")
		print(f"Character count: {self.character_count}")
		print(f"Token count: {self.token_count}")
		print(f"Characters per second: {self.chars_per_second}")
		print(f"Tokens per second: {self.tokens_per_second}")