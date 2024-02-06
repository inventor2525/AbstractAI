from AbstractAI.LLMs.LLM import LLM, LLMStats
from AbstractAI.LLMs.ModelLoader import ModelLoader
from AbstractAI.ConversationModel import *

from ClassyFlaskDB.Flaskify import StaticRoute, Flaskify
from typing import Dict, Any

@Flaskify
class RemoteLLM_Backend:
	@StaticRoute
	def init_model(model_name:str, loader_params:Dict[str, Any]) -> ModelInfo:
		#when less tiered, this method, and make sure it loads the conversation model in an engine before starting
		
		#this is whats called by init, it should return a model info and not start the model
		
		#it should check if the model is already loaded "somehow" (possibly inside ModelLoader? [rather that delete things from mempory]) and return it by model_info.auto_id
		raise NotImplementedError("This method should be implemented by the backend.")
	
	@StaticRoute
	def load_model(self, model_info:ModelInfo):
		#this should be called by the frontend to load the model by model_info.auto_id, if it is not already loaded
		raise NotImplementedError("This method should be implemented by the backend.")
	
class RemoteLLM(LLM):
	def __init__(self, model_name:str, loader_params:Dict[str, Any]):
		self.stats = LLMStats()
		self.model_info = RemoteLLM_Backend.init_model(model_name, loader_params)
	
	def _load_model(self):
		RemoteLLM_Backend.load_model(self.model_info)
		
		
		
		
		
		
		
	#TODO: implement the rest of these methods:
	@abstractmethod
	def _complete_str_into(self, prompt: str, wip_message:Message, stream:bool=False) -> LLM_RawResponse:
		#This is the meat.... how the fuck to do this?
		pass
	
	def _apply_chat_template(self, conversation: Conversation, start_str:str="") -> str:
		#TODO: Call the class's version of this method. We already have the implementation on the client, just call it based on the class name
		raise NotImplementedError("This method should be implemented by the backend.")