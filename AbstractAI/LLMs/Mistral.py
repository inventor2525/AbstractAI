from .HuggingFaceLLM import *
from .CommonRoles import CommonRoles

class Mistral(HuggingFaceLLM):
	def __init__(self, model_name: str="TheBloke/Mistral-7B-Instruct-v0.2-GPTQ", revision:str = "gptq-8bit-32g-actorder_True"):
		super().__init__()
		self.model_name = model_name
		self.revision = revision

	def _load_model(self):
		self.tokenizer = AutoTokenizer.from_pretrained(self.model_name, use_fast=False, trust_remote_code=True)
		self.model = AutoModelForCausalLM.from_pretrained(self.model_name, torch_dtype=torch.float16, low_cpu_mem_usage=True, device_map="auto", trust_remote_code=False, revision=self.revision) 
		
	def start(self):
		super().start()
		self._load_model()
		
		self.role_mapping = {
			CommonRoles.System: "system",
			CommonRoles.User: "user",
			CommonRoles.Assistant: "assistant"
		}
	
	def generate_prompt_str(self, conversation: Conversation, start_str:str="") -> str:
		chat = []
		for message in conversation.message_sequence.messages:
			message_role, user_name = CommonRoles.from_source(message.source)
			chat.append({
				"role":self.role_mapping[message_role],
				"content":message.content
			})
		
		chat_str = self.tokenizer.apply_chat_template(chat, tokenize=False, add_generation_prompt=True)
		if start_str is not None and len(start_str) > 0:
			chat_str = chat_str + start_str
		return chat_str