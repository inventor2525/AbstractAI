from dataclasses import dataclass, field
from AbstractAI.Automation.Agent import Agent
from AbstractAI.Model.Converse import Conversation, Message, Role
from AbstractAI.LLMs.LLM import LLM
from AbstractAI.Tool import Tool
from AbstractAI.UI.Context import Context
from AbstractAI.Model.Converse.MessageSources import CallerInfo
from typing import List, Optional

@dataclass
class SwitchboardAgent(Agent):
	@classmethod
	def default_llm(cls) -> LLM:
		from AbstractAI.Model.Settings.Groq_LLMSettings import Groq_LLMSettings
		llm_settings = next(Context.engine.query(Groq_LLMSettings).all(where="user_model_name = 'llama ToolUser'"))
		if llm_settings is None:
			raise ValueError("LLM settings not found in the database.")
		llm = llm_settings.load()
		llm.start()
		return llm
	
	def __post_init__(self):
		super().__post_init__()

		self.tools = [
			Tool.from_function(self._call_file_changing_agent),
			Tool.from_function(self._call_replacement_agent),
			Tool.from_function(self._call_talk_to_code_agent)
		]

	def __call__(self, conversation: Conversation) -> Conversation:
		stack_trace = CallerInfo.catch([0,1])
		
		switchboard_conv = Conversation("Switchboard", "Routes user requests to appropriate agents") | self.config
		switchboard_conv.props.original_conversation = conversation
		
		system_message = """You are a large language model acting as a switchboard to route user requests to different agents.
Your goal is to analyze the user's request and determine which agent should handle it.
An agent is another large language model specialized for a specific task.
Your job is to match the user's request with the most appropriate specialized agent."""
		
		switchboard_conv + (system_message, Role.System()) | stack_trace
		
		return switchboard_conv

	def chat(self, conversation: Conversation, start_str: str = "", stream: bool = False, max_tokens: int = None) -> Message:
		return self.llm.chat(conversation, start_str=start_str, stream=stream, max_tokens=max_tokens, tools=self.tools)

	def process_response(self, conversation: Conversation):
		response = conversation[-1]
		if self.llm.there_is_tool_call(response):
			tool_messages = self.llm.call_tools(response, tools=self.tools)
			conversation.add_messages(tool_messages)

	def _call_file_changing_agent(self) -> str:
		"""
		Calls the File Changing Agent to modify files or code based on the user's request.
		This agent is specialized in tasks related to file manipulation and code changes.
		"""
		from AbstractAI.Automation.FileChangingAgent import FileChangingAgent
		agent = FileChangingAgent()
		original_conv = Context.conversation.props.original_conversation
		Context.conversation = agent(original_conv)
		return "File Changing Agent has been called and completed its task."

	def _call_replacement_agent(self) -> str:
		"""
		Calls the Replacement Agent to perform text replacement or editing tasks.
		This agent is specialized in modifying existing text or content based on user specifications.
		"""
		from AbstractAI.Automation.ReplacementAgent import ReplacementAgent
		agent = ReplacementAgent()
		original_conv = Context.conversation.props.original_conversation
		Context.conversation = agent(original_conv)
		return "Replacement Agent has been called and completed its task."

	def _call_talk_to_code_agent(self) -> str:
		"""
		Calls the Talk to Code Agent for tasks related to code generation or explanation.
		This agent is specialized in understanding and generating code based on natural language input.
		"""
		from AbstractAI.Automation.TalkToCodeAgent import TalkToCodeAgent
		agent = TalkToCodeAgent()
		original_conv = Context.conversation.props.original_conversation
		Context.conversation = agent(original_conv)
		return "Talk to Code Agent has been called and completed its task."

	@staticmethod
	def call_switchboard(user_message: str):
		original_conversation = Context.conversation
		agent = SwitchboardAgent()
		new_conversation = agent(original_conversation)
		new_conversation + (user_message, Role.User())
		Context.conversation = new_conversation

		response = agent.chat(new_conversation)
		new_conversation.add_message(response)