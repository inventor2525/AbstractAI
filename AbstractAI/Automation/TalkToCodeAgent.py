from AbstractAI.LLMs.LLM import Conversation, Iterator, LLM_Response, Union
from .Agent import *

class TalkToCodeAgent(Agent):
	def __call__(self, message:Message) -> Conversation:
		stack_trace = CallerInfo.catch([0,1])
		
		talk_to_code_conv = Conversation("Talk to code", "A user speaking code to have it converted to text") | stack_trace
		talk_to_code_conv + (r"""You are a speech to code typing assistance device.
					   
		Your output results in typing on the users machine, as though it came from their keyboard. The user will say something which could be poorly transcribed from speech without the context of where they are typing, or it could be malformed or miss spelled. You should take what they say and type clear code as best you can.
					   
		Example:
		User:
		in python for i in range 0 to one hundred print i
		
		Assistant:
		for in range(0,100):
			print(i)
					   
		Notice how there is no extra markdown formatting to the code, or comments by the assistant, only the raw code as the user described.""", Role.System()) | stack_trace
		
		talk_to_code_conv + message
		return talk_to_code_conv
		
	def chat(self, conversation: Conversation, start_str: str = "", stream=False, max_tokens: int = None, auto_append: bool = False) -> LLM_Response | Iterator[LLM_Response]:
		additional_system_message = "That was additional info from the user, again, only respond with code."
		
		# make it so that message exists only ever at the end of the conversation:
		conversation - additional_system_message
		conversation + (additional_system_message, Role.System()) | CallerInfo.catch([0,1])
		
		return self.llm.chat(conversation, start_str=start_str, stream=stream, max_tokens=max_tokens, auto_append=auto_append)
	
	def process_response(self, conversation: Conversation):
		message = conversation[-1]
		return message.content