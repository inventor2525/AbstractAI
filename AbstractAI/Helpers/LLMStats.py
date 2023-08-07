from AbstractAI.Helpers.AMMS import AMMS

class LLMStats:
	def __init__(self):
		self.duration = AMMS()
		self.response_length = AMMS()
		self.token_count = AMMS()
		self.chars_per_second = AMMS()
		self.tokens_per_second = AMMS()
		
	def print(self):
		print(f"Duration: {self.duration}")
		print(f"Response length: {self.response_length}")
		print(f"Token count: {self.token_count}")
		print(f"Characters per second: {self.chars_per_second}")
		print(f"Tokens per second: {self.tokens_per_second}")