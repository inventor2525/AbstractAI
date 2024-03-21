from AbstractAI.ConversationModel import *

from typing import Any, Dict
from dataclasses import dataclass, field
from abc import ABC, abstractmethod

@dataclass
def Condition(ABC):
	name:str = None
	description:str = None
	
	@abstractmethod
	def run(self, conversation:Conversation, context:Dict[str,Any]=None) -> bool:
		raise NotImplementedError("This method must be implemented by a subclass")
	
	def __call__(self, conversation:Conversation, context:Dict[str,Any]=None) -> bool:
		print(f"Running {self.name} with conversation: {conversation} and context: {context}")
		r = self.run(conversation, context)
		print(f"Finished running {self.name}")
		return r

#TODO: the condition class and it's description should be saved in the database
# and a dectorator should be used to create conditions that are then effectively
# loaded from the database as a reference to the decorated function, and the
# documentation should be used to create the default description for the condition.