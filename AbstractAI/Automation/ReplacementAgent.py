from AbstractAI.LLMs.LLM import Conversation, Iterator, LLM_Response, Union
from .Agent import *

class ReplacementAgent(Agent):
	def __call__(self, conversation:Conversation, msg_to_replace:Message) -> Conversation:
		stack_trace = CallerInfo.catch([0,1])
		replacerConv = Conversation(
			f"Message Replacer:{conversation.name}",
			"A conversation about replacing a message in another conversation based on user feedback."
		) | stack_trace
		
		#store some meta data on the conversation:
		replacerConv.props.conversation_under_edit = conversation
		replacerConv.props.msg_to_replace = msg_to_replace
		
		replacerConv + (r"""I want you to replace a message in the following conversation given user feedback and things learned from that conversation as it continued to develop past the point of the message I want you to replace.
		
		Your new version of that message should take a first person role in the shoes of the entity who's message I want you to replace.
		
		Here is the conversation that occurred:
		==============\n"""+str(conversation)+"\n==============",Role.System()) | stack_trace
		
		msg_index = conversation.message_sequence.messages.index(msg_to_replace)
		replacerConv + (f"Now, in first person, without any prefix, re-write message {msg_index}:\n```txt\n{msg_to_replace.content}\n```\n. Do this as though you were in the writers place, but given what was learned latter.", Role.User())
		
		return replacerConv
		
	def chat(self, conversation: Conversation, start_str: str = "", stream=False, max_tokens: int = None, auto_append: bool = False) -> LLM_Response | Iterator[LLM_Response]:
		additional_system_message = "That was more feedback from the user, take it into consideration, revise the message again, and again: keep it in first person without any other prefix or suffix."
		
		# make it so that message exists only ever at the end of the conversation:
		conversation - additional_system_message
		conversation + (additional_system_message, Role.System()) | CallerInfo.catch([0,1])
		
		return self.llm.chat(conversation, start_str=start_str, stream=stream, max_tokens=max_tokens, auto_append=auto_append)
	
	def process_response(self, conversation: Conversation):
		new_message = conversation[-1]
		original_message:Message = conversation.props.msg_to_replace
		edit = original_message & new_message | CallerInfo.catch([0,1])
		
		conversation.apply_edit(edit)