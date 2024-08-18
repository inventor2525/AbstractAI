from AbstractAI.LLMs.LLM import Conversation, Iterator, Union
from .Agent import *
from jinja2 import Template

class ReplacementAgent(Agent):
	def __call__(self, conversation:Conversation, msg_to_replace:Message) -> Conversation:
		stack_trace = CallerInfo.catch([0,1])
		replacerConv = Conversation(
			f"Message Replacer:{conversation.name}",
			"A conversation about replacing a message in another conversation based on user feedback."
		) | self.config
		
		#store some meta data on the conversation:
		replacerConv.props.conversation_under_edit = conversation
		replacerConv.props.msg_to_replace = msg_to_replace

		msg_index = conversation.message_sequence.messages.index(msg_to_replace)

		pre_prompt = ReplacementAgent.conversation_template.render(conversation=str(conversation))
		replacerConv + (pre_prompt, Role.System()) | stack_trace

		rewrite_request = ReplacementAgent.rewrite_template.render(msg_index=msg_index, msg_to_replace=msg_to_replace)
		replacerConv + (rewrite_request, Role.User()) | stack_trace

		return replacerConv

	def chat(self, conversation: Conversation, start_str: str = "", stream=False, max_tokens: int = None) -> Message:
		reminder_message = ReplacementAgent.reminder_template.render()
		
		# make it so that message exists only ever at the end of the conversation:
		conversation - reminder_message
		conversation + (reminder_message, Role.System()) | CallerInfo.catch([0,1])
		
		return self.llm.chat(conversation, start_str=start_str, stream=stream, max_tokens=max_tokens)
	
	def process_response(self, conversation: Conversation):
		new_message = Message(conversation[-1].content, conversation[-1].role, date_created=conversation[-1].date_created) | conversation[-1]
		original_message:Message = conversation.props.msg_to_replace
		edit = original_message & new_message | CallerInfo.catch([0,1])
		
		conversation.props.conversation_under_edit.apply_edit(edit)

ReplacementAgent.conversation_template = Template("""
I want you to replace a message in the following conversation given user feedback and things learned from that conversation as it continued to develop past the point of the message I want you to replace.

Your new version of that message should take a first person role in the shoes of the entity who's message I want to replace.

Here is the conversation that occurred:
==============
{{ conversation }}
==============
""")

ReplacementAgent.rewrite_template = Template("""
Now, in first person, without any prefix, re-write message {{ msg_index }}:
```txt
{{ msg_to_replace.content }}
```
""")
	
ReplacementAgent.reminder_template = Template("""
That was more feedback from the user, take it into consideration, revise the message again, and again: keep it in first person without any other prefix or suffix.
""")