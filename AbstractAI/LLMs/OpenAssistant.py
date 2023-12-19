from .HuggingFaceLLM import *
from .CommonRoles import CommonRoles

class OpenAssistantLLM(HuggingFaceLLM):
	def __init__(self, model_name: str):
		super().__init__()
		self.model_name = model_name

	def start(self):
		super().start()
		self._load_model()
		
		self.role_mapping = {
			CommonRoles.System: "system",
			CommonRoles.User: "prompter",
			CommonRoles.Assistant: "assistant"
		}
	
	def generate_prompt_str(self, conversation: Conversation, start_str:str=""):
		prompt = ""
		for message in conversation.message_sequence.messages:
			message_role, user_name = CommonRoles.from_source(message.source)
			prompt += f"<|{self.role_mapping[message_role]}|>{message.content}</s>"
		prompt += f"<|{self.role_mapping[CommonRoles.Assistant]}|>"
		return prompt+start_str