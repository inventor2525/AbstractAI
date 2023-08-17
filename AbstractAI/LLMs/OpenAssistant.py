from .Message import Message, Role

class OpenAssistantLLM(HuggingFaceLLM):
	def __init__(self, model_name: str):
		super().__init__()
		self.model_name = model_name

	def start(self):
		super().start()
		self.tokenizer = AutoTokenizer.from_pretrained(self.model_name, use_fast=False, trust_remote_code=True)
		self.model = AutoModelForCausalLM.from_pretrained(self.model_name, torch_dtype=torch.float16, low_cpu_mem_usage=True, device_map="auto", trust_remote_code=True)

		self.role_mapping = {
			Role.SYSTEM: "system",
			Role.USER: "prompter",
			Role.ASSISTANT: "assistant"
		}
	
	def prompt_with_conversation(self, conversation: Conversation):
		prompt = self._generate_prompt(conversation)
		return self.prompt(prompt)
	
	def _generate_prompt(self, conversation: Conversation):
		prompt = self._generate_prompt(conversation)
		return self.prompt(prompt)
	
	def _generate_prompt(self, conversation):
		prompt = ""
		for message in conversation.messages:
			prompt += f"<|{self.role_mapping[message.role]}|>{message.content}</s>"
		prompt += f"<|{self.role_mapping[Role.ASSISTANT]}|>"
		return prompt