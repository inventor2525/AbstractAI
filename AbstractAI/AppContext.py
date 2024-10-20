from dataclasses import dataclass, field
from AbstractAI.Model.Converse import *
from AbstractAI.Helpers.Signal import Signal
from AbstractAI.Automation.MainAgent import MainAgent
from ClassyFlaskDB.new.SQLStorageEngine import SQLStorageEngine
from AbstractAI.Helpers.Jobs import Jobs
from argparse import Namespace

@dataclass
class ApplicationContextModel:
	args:Namespace = None
	engine:SQLStorageEngine = None
	transcriber: 'Transcriber' = None
	jobs:Jobs = None
	start_str: str = ""
	storage_location: str = None
	
	llm_loaded: bool = False
	llm_generating: bool = False
	new_message_has_text: bool = False
	main_agent: MainAgent = None
	
	conversation_selected:Signal[[Conversation, Conversation],None] = Signal.field()
	context_changed:Signal[[],None] = Signal.field()
	
	user_source: UserSource = None
	
	active_conversations: List[Conversation] = field(default_factory=list)
	
	@property
	def conversation(self) -> Conversation:
		return getattr(self, "_conversation", None)
	@conversation.setter
	def conversation(self, value:Conversation):
		if self.conversation != value:
			prev_conversation = self.conversation
			self._conversation = value
			
			added_to_active = False
			if value not in self.active_conversations:
				self.active_conversations.append(value)
				added_to_active = True
			self.conversation_selected(prev_conversation, value)
			if added_to_active:
				self.context_changed()
	
	def has_llm(self, conversation: Conversation):
		return self.llm_loaded

AppContext = ApplicationContextModel()

# from AbstractAI.Helpers.Transcriber import Transcriber