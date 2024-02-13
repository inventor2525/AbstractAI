from threading import Thread, Lock
from AbstractAI.ConversationModel import Conversation
from AbstractAI.LLMs.LLM import LLM, LLMStats, LLM_Response
from AbstractAI.LLMs.ModelLoader import ModelLoader
from AbstractAI.ConversationModel import *

from ClassyFlaskDB.Flaskify import StaticRoute, Flaskify
from typing import Dict, Any, List
import json

class StreamResponse:
	'''A class to continuously generate more of a response from a stream until it's done.'''
	def __init__(self, response:LLM_Response):
		self.response = response
		self.done = False
		self.thread = Thread(target=self._generate_more)
		self.lock = Lock()
		self.thread.start()
	
	def stop(self):
		with self.lock:
			self.done = True
	
	def copy_current(self) -> Message:
		with self.lock:
			return self.response.message.deepcopy()
	
	def _generate_more(self):
		while not self.done:
			with self.lock:
				self.done = not self.response.generate_more()
	
	def __del__(self):
		self.stop()
		self.thread.join()

@Flaskify
class RemoteLLM_Backend:
	model_loader : ModelLoader
	models_by_name : Dict[str,LLM]
	models_by_id : Dict[int,LLM]
	streams : Dict[str,StreamResponse]
	
	@Flaskify.ServerInit
	def server_init():
		RemoteLLM_Backend.model_loader = ModelLoader()
		RemoteLLM_Backend.models_by_name = {}
		RemoteLLM_Backend.models_by_id = {}
		RemoteLLM_Backend.streams = {}
		
	@StaticRoute
	def init_model(model_name:str, loader_params:Dict[str, Any]) -> ModelInfo:
		if loader_params is not None and len(loader_params) > 0:
			raise NotImplementedError("add model with dict not implemented yet")
			# RemoteLLM_Backend.model_loader.add_model(model_name, loader_params)
		if model_name not in RemoteLLM_Backend.models_by_name:
			RemoteLLM_Backend.models_by_name[model_name] = RemoteLLM_Backend.model_loader[model_name]
			RemoteLLM_Backend.models_by_id[RemoteLLM_Backend.models_by_name[model_name].model_info.auto_id] = RemoteLLM_Backend.models_by_name[model_name]
		return RemoteLLM_Backend.models_by_name[model_name].model_info
	
	@StaticRoute
	def load_model(model_info:ModelInfo):
		RemoteLLM_Backend.models_by_id[model_info.auto_id].start()
		
	@StaticRoute
	def apply_chat_template(model_info:ModelInfo, chat: List[Dict[str,str]], start_str:str="") -> str:
		return RemoteLLM_Backend.models_by_id[model_info.auto_id]._apply_chat_template(chat, start_str)
	
	@StaticRoute
	def chat(model_info:ModelInfo, conversation: Conversation, start_str: str = "", stream=False) -> Message:
		response = RemoteLLM_Backend.models_by_id[model_info.auto_id].chat(conversation, start_str, stream)
		if stream:
			RemoteLLM_Backend.streams[response.message.source.auto_id] = StreamResponse(response)
		return response.message
	
	@StaticRoute
	def complete_str(model_info:ModelInfo, text:str, stream=False) -> Message:
		response = RemoteLLM_Backend.models_by_id[model_info.auto_id].complete_str(text, stream)
		if stream:
			RemoteLLM_Backend.streams[response.message.source.auto_id] = StreamResponse(response)
		return response.message
	
	@StaticRoute
	def get_continuation(message_id:str) -> Message:
		'''A really lazy slow way to request the updated response from a server side stream'''
		return RemoteLLM_Backend.streams[message_id].copy_current()
	
	@StaticRoute
	def stop_stream(message_id:str):
		RemoteLLM_Backend.streams[message_id].stop()
		del RemoteLLM_Backend.streams[message_id]
	
class RemoteLLM(LLM):
	def __init__(self, model_name:str, loader_params:Dict[str, Any]={}):
		self.stats = LLMStats()
		self.model_info = RemoteLLM_Backend.init_model(model_name, loader_params)
	
	def _load_model(self):
		RemoteLLM_Backend.load_model(self.model_info)
	
	def _gen_remote_response(self, message:Message, stream:bool=False):
		response = LLM_Response(message, message.source.in_token_count, stream)
		if stream:
			def stop_streaming_func():
				RemoteLLM_Backend.stop_stream(message.source.auto_id)
			response.stop_streaming_func = stop_streaming_func
			
			def genenerate_more_func():
				new_msg = RemoteLLM_Backend.get_continuation(message.source.auto_id)
				response.copy_from(new_msg)
			response.genenerate_more_func = genenerate_more_func
		return response
	
	def chat(self, conversation: Conversation, start_str: str = "", stream=False) -> LLM_Response:
		message = RemoteLLM_Backend.chat(self.model_info, conversation, start_str, stream)
		return self._gen_remote_response(message, stream)
	
	def complete_str(self, text:str, stream=False) -> LLM_Response:
		message = RemoteLLM_Backend.complete_str(self.model_info, text, stream)
		return self._gen_remote_response(message, stream)
	
	def _complete_str_into(self, prompt: str, wip_message:Message, stream:bool=False) -> LLM_Response:
		raise NotImplementedError("This should never be called")
	
	def _apply_chat_template(self, chat: List[Dict[str,str]], start_str:str="") -> str:
		RemoteLLM_Backend.apply_chat_template(self.model_info, chat, start_str)