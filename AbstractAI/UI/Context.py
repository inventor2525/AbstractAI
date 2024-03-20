from dataclasses import dataclass, field
from PyQt5.QtCore import QSettings
from AbstractAI.ConversationModel import *
from AbstractAI.LLMs.ModelLoader import ModelLoader
from AbstractAI.Helpers.Signal import Signal

@dataclass
class Context:
	settings: QSettings = None
	model_loader: ModelLoader = None
	llm_loaded: bool = False
	
	conversation_selected:Signal[[],None] = Signal.field()
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
		old_conversation = self.conversation
		self._conversation = value
		if old_conversation != value:
			self.conversation_selected()
		
	def __post_init__(self):
		Context.singleton = self
	
	def has_llm(self, conversation: Conversation):
		return self.llm_loaded

Context = Context.singleton()