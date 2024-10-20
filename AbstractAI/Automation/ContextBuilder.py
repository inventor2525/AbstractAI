from typing import Any
from AbstractAI.Conversable import Conversation
from ClassyFlaskDB.DefaultModel import Object, DATA, dataclass, get_local_time, field
from datetime import datetime
import os

@DATA
@dataclass
class TextContext(Object):
	text: str
	
	@property
	def none_str(self) -> str:
		return ""
	
	def copy(self) -> 'TextContext':
		return TextContext(text=self.text)
	
	def __str__(self):
		if self.text is None:
			return self.none_str
		return self.text

@DATA
@dataclass
class TextFileContext(TextContext):
	path: str
	text: str = field(default=None, init=False)
	
	@property
	def none_str(self) -> str:
		return f"<Context loaded from file path '{self.path}' does not exist>"
	
	def __post_init__(self):
		if os.path.exists(self.path):
			with open(self.path, 'r') as f:
				self.text = f.read()
		else:
			self.text = None
	
	def copy(self) -> 'TextFileContext':
		return TextFileContext(path=self.path)
	
	@staticmethod
	def from_app_dir(inner_dir:str) -> 'TextFileContext':
		'''
		Loads a text file inside the git repo
		that this class is inside of, at a relative
		directory 'inner_dir'
		'''
		repo_root = TextFileContext.get_repo_root_dir()
		full_path = os.path.join(repo_root, inner_dir)
		return TextFileContext(path=full_path)

	@staticmethod
	def get_repo_root_dir() -> str:
		if not hasattr(TextFileContext, '_repo_root'):
			# Get the current file's directory
			current_dir = os.path.dirname(os.path.abspath(__file__))
			
			# Navigate to the root of the git repo
			repo_root = current_dir
			while not os.path.exists(os.path.join(repo_root, '.git')):
				repo_root = os.path.dirname(repo_root)
				if repo_root == os.path.dirname(repo_root):  # Reached the root directory
					raise Exception("Git repository root not found")
			
			TextFileContext._repo_root = repo_root

		return TextFileContext._repo_root

@DATA
@dataclass
class ConversationContext(TextContext):
	conversation:Conversation
	text: str = field(default=None, init=False)
	
	@property
	def none_str(self) -> str:
		return f"In a previous conversation (None): Nothing was said."
	
	def __post_init__(self):
		if self.conversation:
			self.text = f"In a previous conversation named '{self.conversation.name}' we said the following:\n```md\n{str(self.conversation)}\n```\n(End of previous conversation '{self.conversation.name}')"
		else:
			self.text = None
	
	def copy(self) -> 'TextFileContext':
		return TextFileContext(path=self.conversation)