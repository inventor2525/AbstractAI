from .Message import Message, Role
from torch import bfloat16

class StableBeluga2(HuggingFaceLLM):
	def __init__(self, model_name:str):
		super().__init__()
		self.model_name = model_name
	
	def start(self):
		super().start()
		if self.model_name == "stabilityai/StableBeluga2":
			#Load in 4 bit:
			bnb_config = transformers.BitsAndBytesConfig(
				load_in_4bit=True,
				bnb_4bit_quant_type='nf4',
				bnb_4bit_use_double_quant=True,
				bnb_4bit_compute_dtype=bfloat16
			)
			model_config = transformers.AutoConfig.from_pretrained(
				self.model_name,
				#use_auth_token=HF_AUTH
			)

			self.model = transformers.AutoModelForCausalLM.from_pretrained(
				self.model_name,
				trust_remote_code=True,
				config=model_config,
				quantization_config=bnb_config,
				device_map='auto',
				#use_auth_token=HF_AUTH
			)

			self.tokenizer = transformers.AutoTokenizer.from_pretrained(
				self.model_name,
				#use_auth_token=HF_AUTH
			)
		else:
			self.tokenizer = AutoTokenizer.from_pretrained(self.model_name, use_fast=False, trust_remote_code=True)
			self.model = AutoModelForCausalLM.from_pretrained(self.model_name, torch_dtype=torch.float16, low_cpu_mem_usage=True, device_map="auto", trust_remote_code=True)
		
		self.role_mapping = {
			Role.SYSTEM: "System",
			Role.USER: "User",
			Role.ASSISTANT: "Assistant"
		}
	
	def prompt_with_conversation(self, conversation: Conversation):
		prompt = self.generate_prompt(conversation)
		return self.prompt(prompt)
	
	def generate_prompt(self, conversation):
		prompt = ""
		for message in conversation.messages:
			prompt += f"### {self.role_mapping[message.role]}:\n{message.content}\n\n"
		prompt += f"### {self.role_mapping[Role.ASSISTANT]}:"
		return prompt