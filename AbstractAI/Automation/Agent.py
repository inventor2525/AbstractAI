from AbstractAI.LLMs.LLM import *
from ClassyFlaskDB.DefaultModel import Object, DATA, ClassInfo
from AbstractAI.Conversable import Conversable
from AbstractAI.Tool import Tool
from abc import abstractmethod

@DATA
@dataclass
class AgentConfig(Object):
	llm_settings:LLMSettings
	agent_class:str
	tools:List[Tool]

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
			self.tools
		) | CallerInfo.catch([1,2])
		return self.__config__
	
	@abstractmethod
	def __call__(self, *args, **kwargs) -> Conversation:
		pass
	
	@abstractmethod
	def process_response(self, conversation: Conversation):
		pass