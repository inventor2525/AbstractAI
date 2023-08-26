from HuggingFaceLLM import *

class OpenAssistantLLM(HuggingFaceLLM):
	def __init__(self, model_name: str):
		super().__init__()
		self.model_name = model_name

	def start(self):
		super().start()
		self.tokenizer = AutoTokenizer.from_pretrained(self.model_name, use_fast=False, trust_remote_code=True)
		self.model = AutoModelForCausalLM.from_pretrained(self.model_name, torch_dtype=torch.float16, low_cpu_mem_usage=True, device_map="auto", trust_remote_code=True)

		self.role_mapping = {
			Role.System: "system",
			Role.User: "prompter",
			Role.Assistant: "assistant"
		}
	
	def generate_prompt_str(self, conversation: Conversation):
		prompt = ""
		for message in conversation.message_sequence.messages:
			prompt += f"<|{self.role_mapping[message.role]}|>{message.content}</s>"
		prompt += f"<|{self.role_mapping[Role.Assistant]}|>"
		return prompt