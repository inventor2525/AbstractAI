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

@dataclass
class Agent(Conversable):
	llm:LLM
	tools: List[Tool] = None
	
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
	
	@abstractmethod
	def process_response(self, conversation: Conversation):
		pass