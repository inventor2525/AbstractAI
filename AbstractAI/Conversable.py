from abc import ABC, abstractmethod
from AbstractAI.Model.Converse import Conversation, Message, ModelSource
from typing import List, Optional
from AbstractAI.Tool import Tool

class Conversable(ABC):
	@abstractmethod
	def chat(self, conversation: Conversation, start_str:str="", stream=False, max_tokens:int=None) -> Message:
		pass

	@staticmethod
	def continue_message(message: Message) -> bool:
		model_source = message.get_source(ModelSource)
		if model_source and hasattr(model_source, 'continue_function'):
			return model_source.continue_function()
		return False

	@staticmethod
	def stop_message(message: Message):
		model_source = message.get_source(ModelSource)
		if model_source and hasattr(model_source, 'stop_function'):
			model_source.stop_function()

class ToolUser(Conversable):
	@abstractmethod
	def there_is_tool_call(self, message: Message) -> bool:
		pass

	@abstractmethod
	def call_tools(self, message: Message, tools: List[Tool]) -> List[Message]:
		pass

	@abstractmethod
	def chat(self, conversation: Conversation, start_str:str="", stream=False, max_tokens:int=None, tools: List[Tool] = []) -> Message:
		pass