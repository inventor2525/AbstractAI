class PromptGenerator:
	def __init__(self, system_message: str):
		self.system_message = system_message
		self.conversation = ""
		
	def reset(self):
		self.conversation = ""

	def add_prompt(self, user_prompt: str):
		raise NotImplementedError

	def add_response(self, ai_response: str):
		raise NotImplementedError
	
	def get_prompt(self) -> str:
		return self.conversation