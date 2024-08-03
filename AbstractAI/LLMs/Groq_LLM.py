from AbstractAI.LLMs.LLM import LLM, Conversation, Iterator, LLM_Response, Union
from AbstractAI.Conversable import ToolUser
from AbstractAI.Tool import Tool, TOOL_MISSING
from groq import Groq
import json
from typing import List, Dict, Any
from AbstractAI.Model.Settings.Groq_LLMSettings import Groq_LLMSettings

class Groq_LLM(ToolUser, LLM):
	def __init__(self, settings: Groq_LLMSettings):
		super().__init__(settings)
		self.client = None

	def _load_model(self):
		self.client = Groq(api_key=self.settings.api_key)

	def chat(self, conversation: Conversation, start_str: str = "", stream: bool = False, max_tokens: int = None, tools: List[Tool] = []) -> Union[LLM_Response, Iterator[LLM_Response]]:
		wip_message, message_list = self._new_message(conversation, start_str)

		tools_list = [self._tool_to_dict(tool) for tool in tools]

		completion = self.client.chat.completions.create(
			model=self.settings.model_name,
			messages=message_list,
			max_tokens=max_tokens,
			stream=stream,
			tools=tools_list,
			tool_choice="auto" if tools else "none"
		)

		if stream:
			response = LLM_Response(wip_message, completion.close)
			yield response

			for chunk in completion:
				if response.message.append(chunk.choices[0].delta.content):
					response.source.out_token_count += 1
				self._log_chunk(self._dict_from_obj(chunk), wip_message)
				response.source.finished = chunk.choices[0].finish_reason == 'stop'
				
				# Update token counts from x_groq usage
				try:
					usage = chunk.x_groq.usage
					response.source.in_token_count = usage.get("prompt_tokens", response.source.in_token_count)
					response.source.out_token_count = usage.get("completion_tokens", response.source.out_token_count)
				except:
					pass
				
				yield response

			response.source.generating = False
		else:
			response = LLM_Response(wip_message)
			response.source.finished = completion.choices[0].finish_reason == 'stop'
			response.message.content = completion.choices[0].message.content
			response.source.serialized_raw_output = self._dict_from_obj(completion)
			
			if completion.usage:
				response.source.in_token_count = completion.usage.prompt_tokens
				response.source.out_token_count = completion.usage.completion_tokens
			
			# Handle tool calls
			tool_calls = completion.choices[0].message.tool_calls
			if tool_calls:
				for tool_call in tool_calls:
					tool_response = self._execute_tool(tools, tool_call)
					message_list.append({
						"tool_call_id": tool_call.id,
						"role": "tool",
						"name": tool_call.function.name,
						"content": json.dumps(tool_response)
					})
				
				# Get the final response after tool use
				final_completion = self.client.chat.completions.create(
					model=self.settings.model_name,
					messages=message_list
				)
				response.message.content = final_completion.choices[0].message.content
				
				# Update token counts for the final response
				try:
					final_usage = final_completion.x_groq.usage
					response.source.out_token_count += final_usage.get("completion_tokens", 0)
				except:
					pass

		response.source.generating = False
		return response

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

	def _execute_tool(self, tools: List[Tool], tool_call) -> Any:
		for tool in tools:
			if tool.name == tool_call.function.name:
				args = json.loads(tool_call.function.arguments)
				return tool(**args)
		raise ValueError(f"Tool '{tool_call.function.name}' not found")

	def _dict_from_obj(self, obj):
		if hasattr(obj, "__dict__"):
			return {k: self._dict_from_obj(v) for k, v in obj.__dict__.items() if not k.startswith("_")}
		elif isinstance(obj, (list, tuple)):
			return [self._dict_from_obj(item) for item in obj]
		elif isinstance(obj, dict):
			return {k: self._dict_from_obj(v) for k, v in obj.items()}
		else:
			return obj

	def _apply_chat_template(self, chat: List[Dict[str, str]], start_str: str = "") -> str:
		prompt_pieces = []
		for message in chat:
			prompt_pieces.append(f"#{message['role']}:\n{message['content']}")
		return "\n\n".join(prompt_pieces)