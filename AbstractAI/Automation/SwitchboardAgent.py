from dataclasses import dataclass, field
from AbstractAI.Automation.Agent import Agent
from AbstractAI.Model.Converse import Conversation, Message, Role
from AbstractAI.Model.Settings.Groq_LLMSettings import Groq_LLMSettings
from AbstractAI.Tool import Tool
from AbstractAI.UI.Context import Context
from AbstractAI.Model.Converse.MessageSources import CallerInfo
from ClassyFlaskDB.new.SQLStorageEngine import SQLStorageEngine
from typing import List

@dataclass
class SwitchboardAgent(Agent):
    engine: SQLStorageEngine
    llm: 'Groq_LLM' = field(init=False)

    def __post_init__(self):
        groq_settings = next(self.engine.query(Groq_LLMSettings).all(where="user_model_name = 'llama ToolUser'"))
        if groq_settings is None:
            raise ValueError("Groq settings not found in the database.")
        self.llm = groq_settings.load()
        self.llm.start()

    def __call__(self, conversation: Conversation) -> Conversation:
        stack_trace = CallerInfo.catch([0,1])
        
        switchboard_conv = Conversation("Switchboard", "Routes user requests to appropriate agents") | stack_trace
        switchboard_conv.props.original_conversation = conversation
        
        system_message = """You are a large language model acting as a switchboard to route user requests to different agents.
Your goal is to analyze the user's request and determine which agent should handle it.
Available agents are:
1. File Changing Agent: For tasks related to modifying files or code.
2. Replacement Agent: For tasks involving text replacement or editing.
3. Talk to Code Agent: For tasks related to code generation or explanation."""
        
        switchboard_conv + (system_message, Role.System()) | stack_trace
        switchboard_conv + (conversation[-1].content, Role.User()) | stack_trace
        
        tools = [
            Tool.from_function(self._call_file_changing_agent),
            Tool.from_function(self._call_replacement_agent),
            Tool.from_function(self._call_talk_to_code_agent)
        ]
        
        response = self.llm.chat(switchboard_conv, tools=tools)
        switchboard_conv.add_message(response)
        
        if self.llm.there_is_tool_call(response):
            tool_messages = self.llm.call_tools(response, tools=tools)
            switchboard_conv.add_messages(tool_messages)
            final_response = self.llm.chat(switchboard_conv, tools=tools)
            switchboard_conv.add_message(final_response)
        
        return switchboard_conv

    def _call_file_changing_agent(self) -> str:
        from AbstractAI.Automation.FileChangingAgent import FileChangingAgent
        agent = FileChangingAgent(self.llm)
        original_conv = Context.conversation
        result_conv = agent(original_conv)
        Context.conversation = result_conv
        return "File Changing Agent has been called and completed its task."

    def _call_replacement_agent(self) -> str:
        from AbstractAI.Automation.ReplacementAgent import ReplacementAgent
        agent = ReplacementAgent(self.llm)
        original_conv = Context.conversation
        result_conv = agent(original_conv)
        Context.conversation = result_conv
        return "Replacement Agent has been called and completed its task."

    def _call_talk_to_code_agent(self) -> str:
        from AbstractAI.Automation.TalkToCodeAgent import TalkToCodeAgent
        agent = TalkToCodeAgent(self.llm)
        original_conv = Context.conversation
        result_conv = agent(original_conv)
        Context.conversation = result_conv
        return "Talk to Code Agent has been called and completed its task."

def start_switchboard():
    original_conversation = Context.conversation
    agent = SwitchboardAgent(Context.engine)
    new_conversation = agent(original_conversation)
    Context.conversation = new_conversation
    # Process the response and handle any necessary UI updates
    # ...
    Context.conversation = original_conversation