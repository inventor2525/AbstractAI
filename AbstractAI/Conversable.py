from abc import ABC, abstractmethod
from LLMs.LLM_Response import LLM_Response #TODO: remove
from AbstractAI.Model.Converse import *

class Conversable(ABC):
	def chat(self, conversation: Conversation, start_str:str="", stream=False, max_tokens:int=None) -> Union[LLM_Response, Iterator[LLM_Response]]:
		...