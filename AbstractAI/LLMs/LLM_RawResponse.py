from AbstractAI.ConversationModel.Message import Message
from typing import Dict

class LLM_RawResponse:
	def __init__(self, raw_response:object, message:Message, token_counts:Dict[str, int]):
		self.raw_response = raw_response
		self.message = message
		self.token_counts = token_counts