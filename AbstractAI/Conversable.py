from abc import ABC, abstractmethod
from LLMs.LLM_Response import LLM_Response #TODO: remove
from AbstractAI.Model.Converse import *
from AbstractAI.Tool import Tool

class Conversable(ABC):
	def chat(self, conversation: Conversation, start_str:str="", stream=False, max_tokens:int=None) -> Union[LLM_Response, Iterator[LLM_Response]]:
		...

class ToolUser(Conversable):
	@abstractmethod
	def chat(self, conversation, start_string: str, stream: bool = False, max_tokens: int = 100, tools: List[Tool] = []):
		...