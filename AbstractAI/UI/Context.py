from dataclasses import dataclass, field
from PyQt5.QtCore import QSettings
from AbstractAI.Model.Converse import *
from AbstractAI.Helpers.Signal import Signal
from argparse import Namespace

@dataclass
class Context:
	args:Namespace = None
	settings: QSettings = None
	start_str: str = ""
	
	llm_loaded: bool = False
	llm_generating: bool = False
	new_message_has_text: bool = False
	
	conversation_selected:Signal[[Conversation, Conversation],None] = Signal.field()
	context_changed:Signal[[],None] = Signal.field()
	
	@staticmethod
	def singleton() -> 'Context':
		if not hasattr(Context, '_singleton'):
			Context._singleton = Context()
		return Context._singleton
	
	@property
	def conversation(self) -> Conversation:
		return getattr(self, "_conversation", None)
	@conversation.setter
	def conversation(self, value:Conversation):
		if self.conversation != value:
			prev_conversation = self.conversation
			self._conversation = value
			self.conversation_selected(prev_conversation, value)
		
	def __post_init__(self):
		Context.singleton = self
	
	def has_llm(self, conversation: Conversation):
		return self.llm_loaded

Context = Context.singleton()