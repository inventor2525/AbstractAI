from AbstractAI.ConversationModel import *
from AbstractAI.LLMs.LLM import LLM
from AbstractAI.LLMs.RestrictedLLM import *
from dataclasses import dataclass, field

@dataclass #TODO: Make this save to db and load from db, using model info objects to load the LLMs
class Agent:
	planning_llm: LLM
	tool_using_llm: RestrictedLLM = None
	starting_message_sequence: MessageSequence = field(default_factory=MessageSequence)
	tool_use_message: Message = None #dont save this in anything but the source of generated content		
	
	def generate_new_tool_use_message(self):
		msg = "You can use tools, this is how..."
		#TODO: add a better prompt and examples and negative examples of tools
		#up to some limits, max token count, number of examples, etc. And possibly
		#sort them in different ways to make it less deterministic what the agent
		#will respond with and reduce the chance of overfitting.
		self.tool_use_message = Message.HardCoded(msg, system_message=True)
	
	