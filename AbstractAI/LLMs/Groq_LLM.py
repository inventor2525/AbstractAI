from AbstractAI.LLMs.LLM import LLM
from AbstractAI.Conversable import ToolUser
from AbstractAI.Model.Converse import Conversation, Message, Role
from AbstractAI.Tool import Tool, TOOL_MISSING
from AbstractAI.Model.Settings.Groq_LLMSettings import Groq_LLMSettings
from AbstractAI.Model.Converse.MessageSources import ModelSource, ToolSource
from groq import Groq, NOT_GIVEN
import json
from typing import List, Dict, Any, Iterator

class Groq_LLM(ToolUser, LLM):
	def __init__(self, settings: Groq_LLMSettings):
		super().__init__(settings)
		self.client = None

	def _load_model(self):
		self.client = Groq(api_key=self.settings.api_key)

	def chat(self, conversation: Conversation, start_str: str = "", stream: bool = False, max_tokens: int = None, tools: List[Tool] = []) -> Message:
		wip_message, message_list = self._new_message(conversation, start_str)

		tools_list = [self._tool_to_dict(tool) for tool in tools]

		completion = self.client.chat.completions.create(
			model=self.settings.model_name,
			messages=message_list,
			max_tokens=max_tokens,
			stream=stream,
			tools=tools_list if len(tools)>0 else NOT_GIVEN,
			tool_choice="auto" if tools else NOT_GIVEN
		)

		if stream:
			chunk_iterator = iter(completion)

			def continue_function():
				try:
					chunk = next(chunk_iterator)
					if wip_message.append(chunk.choices[0].delta.content):
						wip_message.source.out_token_count += 1
					self._log_chunk(self._dict_from_obj(chunk), wip_message)
					wip_message.source.finished = chunk.choices[0].finish_reason == 'stop'
					
					try:
						if chunk.x_groq and chunk.x_groq.usage:
							usage = chunk.x_groq.usage
							wip_message.source.in_token_count = usage.get("prompt_tokens", wip_message.source.in_token_count)
							wip_message.source.out_token_count = usage.get("completion_tokens", wip_message.source.out_token_count)
					except AttributeError:
						pass

					return True
				except StopIteration:
					wip_message.source.generating = False
					wip_message.source.finished = True
					return False

			wip_message.source.continue_function = continue_function
			wip_message.source.stop_function = completion.close
		else:
			wip_message.content = completion.choices[0].message.content
			wip_message.source.finished = completion.choices[0].finish_reason == 'stop'
			wip_message.source.serialized_raw_output = self._dict_from_obj(completion)
			
			if completion.usage:
				wip_message.source.in_token_count = completion.usage.prompt_tokens
				wip_message.source.out_token_count = completion.usage.completion_tokens

			wip_message.source.generating = False

		return wip_message

	def there_is_tool_call(self, message: Message) -> bool:
		try:
			return len(list(self._tool_calls_from_message(message))) > 0
		except Exception as e:
			return False
	
	def _tool_calls_from_message(self, message:Message) -> Iterator[dict]:
		try:
			raw_output = message.source.serialized_raw_output
			for tool_call in raw_output['choices'][0]['message']['tool_calls']:
				yield tool_call
		except Exception as e:
			try:
				raw_output = message.source.serialized_raw_output
				for chunk in raw_output['Chunks']:
					try:
						tool_calls = chunk["choices"][0]["delta"]["tool_calls"]
						if tool_calls is not None:
							for tool_call in tool_calls:
								yield tool_call
					except Exception as e:
						pass
			except Exception as e:
				pass
		return
	
	def call_tools(self, message: Message, tools: List[Tool]) -> List[Message]:
		tool_messages = []

		for tool_call in self._tool_calls_from_message(message):
			for tool in tools:
				if tool.name == tool_call['function']['name']:
					args = json.loads(tool_call['function']['arguments'])
					result = tool(**args)
					tool_message = Message(
						content=json.dumps(result),
						role=Role("Tool", tool.name)
					)
					tool_message.source = ToolSource(
						tool=tool,
						tool_call_id=tool_call['id'],
						function_name=tool_call['function']['name'],
						function_args=args,
						result=result
					)
					tool_messages.append(tool_message)
					break

		return tool_messages

	def _tool_to_dict(self, tool: Tool) -> Dict[str, Any]:
		return {
			"type": "function",
			"function": {
				"name": tool.name,
				"description": tool.description,
				"parameters": {
					"type": "object",
					"properties": {param.name: {"type": param.type, "description": param.description} for param in tool.parameters.values()},
					"required": [param.name for param in tool.parameters.values() if param.default is TOOL_MISSING]
				}
			}
		}