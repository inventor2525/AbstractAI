from typing import Any, List
from ClassyFlaskDB.DefaultModel import Object, DATA, dataclass, get_local_time, field
from datetime import datetime
import os

@DATA
@dataclass
class TextArtifact(Object):
	text: str
	
	@property
	def none_str(self) -> str:
		return ""
	
	def __post_init__(self):
		self.update()
	
	def update(self):
		pass
	
	def copy(self) -> 'TextArtifact':
		return TextArtifact(text=self.text)
	
	def __str__(self):
		if self.text is None:
			return self.none_str
		return self.text

@DATA
@dataclass
class TextArtifacts(TextArtifact):
	artifacts: List[TextArtifact]
	separator: str
	text: str = field(default=None, init=False)
	
	def update(self):
		self.text = self.separator.join([artifact.text for artifact in self.artifacts])
	
@DATA
@dataclass
class TextFileArtifact(TextArtifact):
	path: str
	text: str = field(default=None, init=False)
	
	@property
	def none_str(self) -> str:
		return f"<Context loaded from file path '{self.path}' does not exist>"
	
	def update(self):
		if os.path.exists(self.path):
			with open(self.path, 'r') as f:
				self.text = f.read()
		else:
			self.text = None
	
	def copy(self) -> 'TextFileArtifact':
		return TextFileArtifact(path=self.path)
	
	@staticmethod
	def from_app_dir(inner_dir:str) -> 'TextFileArtifact':
		'''
		Loads a text file inside the git repo
		that this class is inside of, at a relative
		directory 'inner_dir'
		'''
		repo_root = TextFileArtifact.get_repo_root_dir()
		full_path = os.path.join(repo_root, inner_dir)
		return TextFileArtifact(path=full_path)

	@staticmethod
	def get_repo_root_dir() -> str:
		if not hasattr(TextFileArtifact, '_repo_root'):
			# Get the current file's directory
			current_dir = os.path.dirname(os.path.abspath(__file__))
			
			# Navigate to the root of the git repo
			repo_root = current_dir
			while not os.path.exists(os.path.join(repo_root, '.git')):
				repo_root = os.path.dirname(repo_root)
				if repo_root == os.path.dirname(repo_root):  # Reached the root directory
					raise Exception("Git repository root not found")
			
			TextFileArtifact._repo_root = repo_root

		return TextFileArtifact._repo_root