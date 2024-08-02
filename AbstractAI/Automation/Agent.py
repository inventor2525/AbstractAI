from AbstractAI.LLMs.LLM import *
from AbstractAI.Conversable import Conversable
from abc import ABC, abstractmethod

@dataclass
class Agent(Conversable):
	llm:LLM
	
	@abstractmethod
	def __call__(self, *args, **kwargs) -> Conversation:
		pass
	
	@abstractmethod
	def process_response(self, conversation: Conversation):
		pass