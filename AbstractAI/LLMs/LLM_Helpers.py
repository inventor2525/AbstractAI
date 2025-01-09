from enum import Enum
from ClassyFlaskDB.DefaultModel import *
from AbstractAI.Helpers.ScopeParams import ScopeParamsModel
from AbstractAI.Helpers.Jobs import Job, Jobs, JobStatus, WaitFor
from AbstractAI.Model.Converse import Conversation, Message, Role, MessageSequence, CallerInfo
from AbstractAI.LLMs.LLM import LLM
from AbstractAI.Model.Settings.LLMSettings import LLMSettings
from typing import List, Dict, Any, Optional

import inspect
from functools import wraps
from dataclasses import fields
import traceback
import linecache

@DATA
@dataclass
class ResponseObject(Object):
	before_message_sequence: MessageSequence
	after_prompt_message_sequence: MessageSequence
	after_response_message_sequence: MessageSequence = None
	message: Message = None
	job: 'LLMJob' = None
	stacktrace: str = None
	key: str = None

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
class LLMParams(ScopeParamsModel):
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

def get_stacktrace():
    stack = inspect.stack()[1:]
    traceback = []
    for frame_info in reversed(stack):
        filename = frame_info.filename
        lineno = frame_info.lineno
        function = frame_info.function
        line = linecache.getline(filename, lineno).strip()
        traceback.append(f'File "{filename}", line {lineno}, in {function}')
        traceback.append(f'  {line}')
    return "\n".join(traceback)

def llm_job(llm:LLM, prompt:str, conversation:Conversation=None, source:Object=None, key:str=None, blocking:bool=True) -> ResponseObject:
	stacktrace=get_stacktrace() # Useful for self coding personal assistants to know where their own messages came from to aid them in self alteration.
	
	if conversation is None:
		conversation = Conversation(key, stacktrace) | source
	before_message_sequence = conversation.message_sequence
	
	conversation + Message(prompt, Role.User()) | source
	
	after_prompt_message_sequence = conversation.message_sequence
	
	response = ResponseObject(
		before_message_sequence=before_message_sequence,
		after_prompt_message_sequence=after_prompt_message_sequence,
		key=key
	) | source
	
	with LLMParams():
		llm_params = LLMParams.get_all_params()
		job = LLMJob(
			job_key="LLM Chat",
			llm_settings=llm.settings,
			message_sequence=after_prompt_message_sequence,
			llm_params=llm_params,
			response=response
		) | source
		
		response.job = job
		
		if blocking:
			Jobs.singleton().execute_job(job)
		else:
			Jobs.singleton().add(job)
		
		return response

def llm_method(llm: LLM, key:str=None, with_history: bool = False, blocking: bool = True):
	'''
	Method decorator that turns a str returning method into a call
	to the supplied llm. Work is persisted in storage incase failure
	and executed by Jobs.singleton() (optionally) concurrently.
	
	Args:
		llm: The model your str will be sent to in the form of a 'Message'.
		key: An optional string you can use to identify this type of call for self coding agents to refer to.
		with_history: If true, your first argument must be a 'Conversation' that will be used to persist a back and forth chat.
		blocking: If this call will block the current thread or run concurrently.

	Returns:
		A 'ResponseObject' that can be used to return the conversation to any point easily or get the str return from the llm, that also contains metadata useful for the agent to assist the user in message feedback annotation and example curation.
	'''
	constructor = CallerInfo.catch([0,1])
	def decorator(func):
		@wraps(func)
		def wrapper(*args, **kwargs):
			signature = inspect.signature(func)
			bound_args = signature.bind(*args, **kwargs)
			bound_args.apply_defaults()
			
			conversation = None
			if with_history:
				assert isinstance(bound_args.arguments[next(iter(bound_args.arguments))], Conversation), \
					"First argument must be of type Conversation when with_history is True"
				conversation = bound_args.arguments[next(iter(bound_args.arguments))]
		
			return llm_job(llm, func(*args, **kwargs), conversation=conversation, source=constructor, key=key, blocking=blocking)
			

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
