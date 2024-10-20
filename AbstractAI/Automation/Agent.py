from AbstractAI.LLMs.LLM import *
from ClassyFlaskDB.DefaultModel import Object, DATA, ClassInfo
from AbstractAI.Conversable import Conversable
from AbstractAI.Tool import Tool
from abc import abstractmethod

@DATA(excluded_fields=["__agent__"])
@dataclass
class AgentConfig(Object):
	llm_settings:LLMSettings
	agent_class:str
	tools:List[Tool]
	__agent__:"Agent" = field(default=None, kw_only=True)
	
	@property
	def agent(self) -> "Agent":
		if self.__agent__ is None:
			#TODO: load the agent from the saved fields
			raise NotImplemented("agent loading from file not implemented")
		return self.__agent__
	
	@staticmethod
	def get_agent(conversation:Conversation) -> Optional["Agent"]:
		if conversation is None:
			return None
		agent_config = conversation.get_source(AgentConfig)
		if agent_config:
			return agent_config.agent
		return None

@dataclass
class Agent(Conversable):
	llm:LLM = field(default=None, kw_only=True)
	tools: List[Tool] = None
	
	def __post_init__(self):
		if self.llm is None:
			self.llm = self.default_llm()
	
	@classmethod
	def default_llm(cls) -> LLM:
		from AbstractAI.AppContext import AppContext
		from AbstractAI.Model.Settings.Anthropic_LLMSettings import Anthropic_LLMSettings
		llm_settings = next(AppContext.engine.query(Anthropic_LLMSettings).all(where="user_model_name = 'Sonnet 3.5'"))
		if llm_settings is None:
			raise ValueError("LLM settings not found in the database.")
		llm = llm_settings.load()
		llm.start()
		return llm
	
	@property
	def config(self) -> AgentConfig:
		if hasattr(self, "__config__"):
			return self.__config__
		self.__config__ = AgentConfig(
			self.llm.settings,
			ClassInfo.get_semi_qual_name(type(self)),
			self.tools,
			__agent__=self
		) | CallerInfo.catch([1,2])
		return self.__config__
	
	@abstractmethod
	def __call__(self, *args, **kwargs) -> Conversation:
		pass
	
	def chat(self, conversation: Conversation, start_str: str = "", stream=False, max_tokens: int = None) -> Message:
		return self.llm.chat(conversation, start_str=start_str, stream=stream, max_tokens=max_tokens)
	
	@abstractmethod
	def process_response(self, conversation: Conversation):
		pass