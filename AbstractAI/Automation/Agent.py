from AbstractAI.LLMs.LLM import *
from abc import ABC, abstractmethod

@dataclass
class Agent(ABC):
	llm:LLM
	
	@abstractmethod
	def __call__(self, *args, **kwargs) -> Conversation:
		pass
	
	@abstractmethod
	def chat(self, conversation: Conversation, start_str:str="", stream=False, max_tokens:int=None, auto_append:bool=False) -> Union[LLM_Response, Iterator[LLM_Response]]:
		pass
	
	@abstractmethod
	def process_response(self, conversation: Conversation):
		pass