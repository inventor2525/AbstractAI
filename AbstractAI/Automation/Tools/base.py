from typing import Any, List
from dataclasses import dataclass, field
from abc import ABC, abstractmethod

@dataclass #TODO: Mark high reviewed examples, save to db, and load into this based on tool type
class ToolExample:
	user_input: str
	expected_output: str

@dataclass
class ToolNegativeExample:
	user_input: str
	unexpected_output: str
	description: str = None
	
@dataclass
class Tool(ABC):
	name: str = None
	short_description: str = None
	long_description: str = None
	examples: List[ToolExample] = field(default_factory=list)
	negative_examples: List[ToolNegativeExample] = field(default_factory=list)
	
	def __post_init__(self):
		if self.name is None:
			self.name = self.__class__.__name__
		if self.short_description is None:
			self.short_description = self.__doc__.strip()
		if self.long_description is None:
			self.long_description = self.run.__doc__.strip()
	
	@abstractmethod
	def run(self, *args: Any, **kwds: Any) -> Any:
		raise NotImplementedError("This method must be implemented by a subclass")
	
	def __call__(self, *args: Any, **kwds: Any) -> Any:
		print(f"Running {self.name} with args: {args} and kwds: {kwds}")
		r = self.run(*args, **kwds)
		print(f"Finished running {self.name}")
		return r