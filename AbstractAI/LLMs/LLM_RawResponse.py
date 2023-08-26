from AbstractAI.Conversation.Message import Message

class LLM_RawResponse:
	def __init__(self, raw_response:object, message:Message, token_count:int):
		self.raw_response = raw_response
		self.message = message
		self.token_count = token_count