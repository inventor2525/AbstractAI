import argparse
from AbstractAI.Helpers.nvidia_smi import nvidia_smi

# Parse command-line arguments
parser = argparse.ArgumentParser(description='Process some integers.')
parser.add_argument('--model_name', type=str, default="OpenAssistant/falcon-7b-sft-mix-2000",
					help='The model name to use')
parser.add_argument('--system_message', type=str, default="You are a helpful assistant.",
					help='A pre message before all prompts that gets the model into the right frame of mind')
args = parser.parse_args()

# Extract the args
model_name = args.model_name
SYSTEM_MESSAGE = args.system_message

print("..............................................................")
print("..............................................................")
print("..............................................................")
print("..............................................................")
print("..............................................................")
print("-------------------------Running test-------------------------")
print(f"............{model_name}.............")
print("..............................................................")
print("..............................................................")
print("..............................................................")
print("..............................................................")

class OpenAssistantLLM(LLM):
	def __init__(self, model_name: str):
		super().__init__()
		self.model_name = model_name

	def start(self):
		super().start()
		self.tokenizer = AutoTokenizer.from_pretrained(self.model_name, use_fast=False, trust_remote_code=True)
		self.model = AutoModelForCausalLM.from_pretrained(self.model_name, torch_dtype=torch.float16, low_cpu_mem_usage=True, device_map="auto", trust_remote_code=True)

class StableBeluga2(LLM):
	def __init__(self):
		super().__init__()
		self.model_name = "stabilityai/StableBeluga2"
	
	def start(self):
		super().start()
		# self.tokenizer = AutoTokenizer.from_pretrained(self.model_name, use_fast=False, trust_remote_code=True)
		# self.model = AutoModelForCausalLM.from_pretrained(self.model_name, torch_dtype=torch.float16, low_cpu_mem_usage=True, device_map="auto", trust_remote_code=True)

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

class PromptGenerator:
	def __init__(self, system_message: str):
		self.system_message = system_message
		self.conversation = ""

	def add_prompt(self, user_prompt: str):
		raise NotImplementedError

	def add_response(self, ai_response: str):
		raise NotImplementedError
	
	def get_prompt(self) -> str:
		return self.conversation

class OpenAssistantPromptGenerator(PromptGenerator):
	def __init__(self, system_message: str):
		super().__init__(system_message)
		self.conversation = f"""<|system|>{self.system_message}</s>"""
		
	def add_prompt(self, user_prompt):
		self.conversation += f"<|prompter|>{user_prompt}</s>"

	def add_response(self, ai_response):
		self.conversation += f"<|assistant|>{ai_response}</s>"
	
	def get_prompt(self) -> str:
		return f"{self.conversation}<|assistant|>"

class StableBeluga2PromptGenerator(PromptGenerator):
	def __init__(self, system_message: str):
		super().__init__(system_message)
		self.conversation = f"""### System:\n{system_message}\n\n"""
		
	def add_prompt(self, user_prompt):
		self.conversation += f"""### User:\n{user_prompt}\n\n"""

	def add_response(self, ai_response):
		self.conversation += f"### Assistant:\n{ai_response}\n\n"""
	
	def get_prompt(self) -> str:
		return f"{self.conversation}### Assistant:"""

nvidia_smi()
	
# Use the classes
print("Start Loading...", datetime.now())
llm = StableBeluga2()
llm.start()
print("Done Loading!", datetime.now())

nvidia_smi()

def generate_text(user_prompt: str):
	print("Prompting...\n\n\n\n\n")
	prompt_generator = StableBeluga2PromptGenerator(SYSTEM_MESSAGE)
	prompt_generator.add_prompt(user_prompt)
	
	response = llm.timed_prompt(prompt_generator.get_prompt())
	
	prompt_generator.add_response(response)
	print(prompt_generator.conversation)
	nvidia_smi()

# Call the function for different prompts
for i in range(0,2):
	generate_text("Write me a poem please")
	generate_text("Write me a vector3 class in python with lots of useful math functions")
	generate_text("Write me a python quaternion class with lots of useful math functions.")
	generate_text("Write me a vhdl binary counter")
	generate_text("Write me a vhdl 4 pin stepper motor controller.")
	generate_text("Write me a implementation of pure pursuit in python that shows it's results with matplot lib.")
	generate_text("List a bunch of tasks that could stress test you.")
	generate_text("what series of terminal commands could I use to make a folder, put a new py file inside it, add some simple test code to it, and commit the work for that folder in a git repo. Assume everything is installed already.")