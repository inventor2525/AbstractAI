from threading import Thread, Lock
from AbstractAI.ConversationModel import Conversation
from AbstractAI.LLMs.LLM import LLM, LLMStats, LLM_Response
from AbstractAI.LLMs.ModelLoader import ModelLoader
from AbstractAI.ConversationModel import *
from AbstractAI.Helpers.FairLock import FairLock
from AbstractAI.Helpers.Stopwatch import Stopwatch

from ClassyFlaskDB.Flaskify import StaticRoute, Flaskify
from typing import Dict, Any, List
import json

from copy import deepcopy

class StreamResponse:
	'''A class to continuously generate more of a response from a stream until it's done.'''
	def __init__(self, response:LLM_Response):
		self.response = response
		self.done = False
		self.thread = Thread(target=self._generate_more)
		self.lock = FairLock()
		self.thread.start()
	
	def stop(self):
		self.done = True
	
	def copy_current(self) -> Message:
		m:Message = None
		with self.lock:
			with Stopwatch.singleton.timed_block("StreamResponse.copy_current deepcopy"):
				m = deepcopy(self.response.message)
		return m
	
	def _generate_more(self):
		while not self.done:
			with self.lock:
				Stopwatch.singleton.stop("StreamResponse._generate_more off time")
				with Stopwatch.singleton.timed_block("StreamResponse._generate_more generating"):
					self.done = not self.response.generate_more()
				if not self.done:
					Stopwatch.singleton.start("StreamResponse._generate_more off time")
	
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
		with Stopwatch.singleton.timed_block("RemoteLLM.server_init"):
			RemoteLLM_Backend.model_loader = ModelLoader()
			RemoteLLM_Backend.models_by_name = {}
			RemoteLLM_Backend.models_by_id = {}
			RemoteLLM_Backend.streams = {}
		
	@StaticRoute
	def init_model(model_name:str, loader_params:Dict[str, Any]) -> ModelInfo:
		with Stopwatch.singleton.timed_block("RemoteLLM.init_model"):
			if loader_params is not None and len(loader_params) > 0:
				raise NotImplementedError("add model with dict not implemented yet")
				# RemoteLLM_Backend.model_loader.add_model(model_name, loader_params)
			if model_name not in RemoteLLM_Backend.models_by_name:
				RemoteLLM_Backend.models_by_name[model_name] = RemoteLLM_Backend.model_loader[model_name]
				RemoteLLM_Backend.models_by_id[RemoteLLM_Backend.models_by_name[model_name].model_info.auto_id] = RemoteLLM_Backend.models_by_name[model_name]
			return RemoteLLM_Backend.models_by_name[model_name].model_info
	
	@StaticRoute
	def load_model(model_info:ModelInfo):
		with Stopwatch.singleton.timed_block("RemoteLLM.load_model"):
			RemoteLLM_Backend.models_by_id[model_info.auto_id].start()
		
	@StaticRoute
	def apply_chat_template(model_info:ModelInfo, chat: List[Dict[str,str]], start_str:str="") -> str:
		with Stopwatch.singleton.timed_block("RemoteLLM.apply_chat_template"):
			return RemoteLLM_Backend.models_by_id[model_info.auto_id]._apply_chat_template(chat, start_str)
	
	@StaticRoute
	def chat(model_info:ModelInfo, conversation: Conversation, start_str: str = "", stream=False) -> Message:
		with Stopwatch.singleton.timed_block("RemoteLLM.chat"):
			response = RemoteLLM_Backend.models_by_id[model_info.auto_id].chat(conversation, start_str, stream)
			if stream:
				RemoteLLM_Backend.streams[response.message.source.auto_id] = StreamResponse(response)
			return response.message
	
	@StaticRoute
	def complete_str(model_info:ModelInfo, text:str, stream=False) -> Message:
		with Stopwatch.singleton.timed_block("RemoteLLM.complete_str"):
			response = RemoteLLM_Backend.models_by_id[model_info.auto_id].complete_str(text, stream)
			if stream:
				RemoteLLM_Backend.streams[response.message.source.auto_id] = StreamResponse(response)
			return response.message
	
	@StaticRoute
	def get_continuation(message_id:str) -> Message:
		'''A really lazy slow way to request the updated response from a server side stream'''
		with Stopwatch.singleton.timed_block("RemoteLLM.get_continuation"):
			m = RemoteLLM_Backend.streams[message_id].copy_current()
			return m
	
	@StaticRoute
	def stop_stream(message_id:str):
		with Stopwatch.singleton.timed_block("RemoteLLM.stop_stream"):
			RemoteLLM_Backend.streams[message_id].stop()
			del RemoteLLM_Backend.streams[message_id]
	
class RemoteLLM(LLM):
	def __init__(self, model_name:str, loader_params:Dict[str, Any]={}):
		self.stats = LLMStats()
		self.model_info = RemoteLLM_Backend.init_model(model_name, loader_params)
		self.started = False
		
	def _load_model(self):
		with Stopwatch.singleton.timed_block("RemoteLLM.load_model"):
			RemoteLLM_Backend.load_model(self.model_info)
	
	def _gen_remote_response(self, message:Message, stream:bool=False):
		response = LLM_Response(message, message.source.in_token_count, stream)
		if stream:
			def stop_streaming_func():
				with Stopwatch.singleton.timed_block("RemoteLLM.stop_stream"):
					RemoteLLM_Backend.stop_stream(message.source.auto_id)
			response.stop_streaming_func = stop_streaming_func
			
			def genenerate_more_func():
				with Stopwatch.singleton.timed_block("RemoteLLM.get_continuation"):
					new_msg = RemoteLLM_Backend.get_continuation(message.source.auto_id)
					response.copy_from(new_msg)
					return not new_msg.source.finished
			response.genenerate_more_func = genenerate_more_func
		return response
	
	def chat(self, conversation: Conversation, start_str: str = "", stream=False) -> LLM_Response:
		with Stopwatch.singleton.timed_block("RemoteLLM.chat"):
			message = RemoteLLM_Backend.chat(self.model_info, conversation, start_str, stream)
			return self._gen_remote_response(message, stream)
	
	def complete_str(self, text:str, stream=False) -> LLM_Response:
		with Stopwatch.singleton.timed_block("RemoteLLM.complete_str"):
			message = RemoteLLM_Backend.complete_str(self.model_info, text, stream)
			return self._gen_remote_response(message, stream)
		
	def _complete_str_into(self, prompt: str, wip_message:Message, stream:bool=False) -> LLM_Response:
		raise NotImplementedError("This should never be called")
	
	def _apply_chat_template(self, chat: List[Dict[str,str]], start_str:str="") -> str:
		RemoteLLM_Backend.apply_chat_template(self.model_info, chat, start_str)