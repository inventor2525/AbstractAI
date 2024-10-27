from enum import Enum
from ClassyFlaskDB.DefaultModel import *
from AbstractAI.Helpers.ScopeParams import ScopeParams
from AbstractAI.Helpers.Jobs import Job, Jobs, JobStatus, WaitFor
from AbstractAI.Model.Converse import Conversation, Message, Role, MessageSequence
from AbstractAI.LLMs.LLM import LLM
from AbstractAI.Model.Settings.LLMSettings import LLMSettings
from typing import List, Dict, Any, Optional

import inspect
from functools import wraps
from dataclasses import fields
import traceback

@DATA
@dataclass
class ResponseObject:
	before_message_sequence: MessageSequence
	after_prompt_message_sequence: MessageSequence
	after_response_message_sequence: MessageSequence = None
	message: Message = None
	job: 'LLMJob' = None

	@property
	def conversation(self) -> Conversation:
		return self.before_message_sequence.conversation

	def __str__(self) -> str:
		return self.message.content if self.message else ""

	def return_to_before(self) -> Conversation:
		self.conversation.message_sequence = self.before_message_sequence
		return self.conversation
	
	def return_to_after_prompt(self) -> Conversation:
		self.conversation.message_sequence = self.after_prompt_message_sequence
		return self.conversation
	
	def return_to_after_response(self) -> Conversation:
		self.conversation.message_sequence = self.after_response_message_sequence
		return self.conversation

	def __getattribute__(self, name):
		value = object.__getattribute__(self, name)
		if value is None and self.job and not self.job.done:
			self.job.wait()
			value = object.__getattribute__(self, name)
		return value

@dataclass
class LLMParams(ScopeParams):
	stream: bool = False
	max_tokens: Optional[int] = None
	temperature: Optional[float] = None
	top_p: Optional[float] = None

	def __post_init__(self):
		params = {f.name: getattr(self, f.name) for f in fields(self) if getattr(self, f.name) is not None}
		super().__init__(**params)

@DATA
@dataclass
class LLMJob(Job):
	llm_settings: LLMSettings
	message_sequence: MessageSequence
	llm_params: Dict[str, Any]
	response: ResponseObject

def llm_job_work(job: LLMJob) -> JobStatus:
	try:
		conversation = job.message_sequence.conversation
		conversation.message_sequence = job.message_sequence
		
		llm = job.llm_settings.model
		
		# Filter LLM params based on the chat method's signature
		chat_params = inspect.signature(llm.chat).parameters
		filtered_params = {k: v for k, v in job.llm_params.items() if k in chat_params}
		
		message = llm.chat(conversation, **filtered_params)
		conversation + message
		
		job.response.message = message
		job.response.after_response_message_sequence = conversation.message_sequence
		
		if job.llm_params.get('stream', False):
			while llm.continue_message(message):
				if job.should_stop:
					llm.stop_message(message)
					return JobStatus.STOPPED
		
		return JobStatus.SUCCESS
	except Exception as e:
		job.status = f"Error: {str(e)}"
		job.status_hover = traceback.format_exc()
		return JobStatus.FAILED

def llm_job_callback(job: LLMJob):
	# Callback stub
	pass

Jobs.register("LLM Chat", llm_job_work, llm_job_callback)

def llm_method(jobs:Jobs, llm: LLM, with_history: bool = False, blocking: bool = True):
	def decorator(func):
		@wraps(func)
		def wrapper(*args, **kwargs):
			signature = inspect.signature(func)
			bound_args = signature.bind(*args, **kwargs)
			bound_args.apply_defaults()
			
			if with_history:
				assert isinstance(bound_args.arguments[next(iter(bound_args.arguments))], Conversation), \
					"First argument must be of type Conversation when with_history is True"
				conversation = bound_args.arguments[next(iter(bound_args.arguments))]
			else:
				conversation = Conversation()
			
			before_message_sequence = conversation.message_sequence
			
			prompt = func(*args, **kwargs)
			conversation + Message(prompt, Role.User())
			
			after_prompt_message_sequence = conversation.message_sequence
			
			response = ResponseObject(
				before_message_sequence=before_message_sequence,
				after_prompt_message_sequence=after_prompt_message_sequence
			)
			
			with LLMParams():
				llm_params = LLMParams.get_all_params()
				llm_job = LLMJob(
					job_key="LLM Chat",
					llm_settings=llm.settings,
					message_sequence=after_prompt_message_sequence,
					llm_params=llm_params,
					response=response
				)
				
				response.job = llm_job
				
				jobs.add(llm_job)
				
				if blocking:
					llm_job.wait()
				
				return response

		# Update return type hint and docstring
		original_annotations = func.__annotations__.copy()
		original_annotations['return'] = ResponseObject
		wrapper.__annotations__ = original_annotations
		
		if func.__doc__:
			wrapper.__doc__ = func.__doc__.replace(
				"-> str",
				"-> ResponseObject"
			)
		
		return wrapper
	return decorator
