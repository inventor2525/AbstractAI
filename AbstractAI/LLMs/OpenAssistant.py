from .HuggingFaceLLM import *
from .CommonRoles import CommonRoles

class OpenAssistantLLM(HuggingFaceLLM):
	def __init__(self, model_name: str):
		super().__init__()
		self.model_name = model_name

	def start(self):
		super().start()
		self.tokenizer = AutoTokenizer.from_pretrained(self.model_name, use_fast=False, trust_remote_code=True)
		self.model = AutoModelForCausalLM.from_pretrained(self.model_name, torch_dtype=torch.float16, low_cpu_mem_usage=True, device_map="auto", trust_remote_code=True)

		self.role_mapping = {
			CommonRoles.System: "system",
			CommonRoles.User: "prompter",
			CommonRoles.Assistant: "assistant"
		}
	
	def generate_prompt_str(self, conversation: Conversation):
		prompt = ""
		for message in conversation.message_sequence.messages:
			message_role, user_name = CommonRoles.from_source(message.source)
			prompt += f"<|{self.role_mapping[message_role]}|>{message.content}</s>"
		prompt += f"<|{self.role_mapping[CommonRoles.Assistant]}|>"
		return prompt