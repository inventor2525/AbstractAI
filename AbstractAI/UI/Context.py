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
	
	context_changed:Signal[[],None] = Signal.field()
	
	@staticmethod
	def singleton() -> 'Context':
		if not hasattr(Context, '_singleton'):
			Context._singleton = Context()
		return Context._singleton
	
	def __post_init__(self):
		Context.singleton = self
	
	def has_llm(self, conversation: Conversation):
		return self.llm_loaded

Context = Context.singleton()