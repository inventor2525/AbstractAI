#modified from from https://huggingface.co/OpenAssistant/llama2-13b-orca-v2-8k-3166 & https://huggingface.co/OpenAssistant/llama2-13b-orca-8k-3319
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from datetime import datetime
import subprocess
import argparse
import numpy as np

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


# Define base classes
class LLM:
	def __init__(self):
		self.model = None
		self.tokenizer = None

	def start(self):
		raise NotImplementedError

	def respond(self, prompt: str, del_token_type_ids:bool=True):
		inputs = self.tokenizer(prompt, return_tensors="pt").to("cuda")
		try:
			if del_token_type_ids:
				del inputs["token_type_ids"]
		except Exception as e:
			pass
		output = self.model.generate(**inputs, do_sample=True, top_p=0.95, top_k=0, max_new_tokens=1024)
		return output

class AMMS:
	def __init__(self):
		self.values = []
	
	def add(self, value):
		self.values.append(value)
	
	def current(self):
		return self.values[-1]
	
	def average(self):
		return np.mean(self.values)
	
	def min(self):
		return np.min(self.values)
	
	def max(self):
		return np.max(self.values)
	
	def std(self):
		return np.std(self.values)
	
	def __str__(self):
		return f"current={self.current():.2f} average={self.average():.2f} min={self.min():.2f} max={self.max():.2f} std={self.std():.2f}"

class LLMStats:
	def __init__(self):
		self.duration = AMMS()
		self.response_length = AMMS()
		self.token_count = AMMS()
		self.chars_per_second = AMMS()
		self.tokens_per_second = AMMS()
		
	def print(self):
		print(f"Duration: {self.duration}")
		print(f"Response length: {self.response_length}")
		print(f"Token count: {self.token_count}")
		print(f"Characters per second: {self.chars_per_second}")
		print(f"Tokens per second: {self.tokens_per_second}")
		
class OpenAssistantLLM(LLM):
	def __init__(self, model_name: str):
		super().__init__()
		self.model_name = model_name
		self.stats = LLMStats()

	def start(self):
		print(f"\n\n\nLoading LLM \"{self.model_name}\"...\n\n\n")
		self.tokenizer = AutoTokenizer.from_pretrained(self.model_name, use_fast=False, trust_remote_code=True)
		self.model = AutoModelForCausalLM.from_pretrained(self.model_name, torch_dtype=torch.float16, low_cpu_mem_usage=True, device_map="auto", trust_remote_code=True)

	def timed_prompt(self, prompt: str):
		start_time = datetime.now()
		output = self.respond(prompt)
		generated_text = self.tokenizer.decode(output[0], skip_special_tokens=True)
		end_time = datetime.now()
		
		print(f"Start time: {start_time}")
		print(f"End time: {end_time}")
		
		duration_seconds = (end_time - start_time).total_seconds()
		token_count = len(output[0])
		
		self.stats.duration.add(duration_seconds)
		self.stats.response_length.add(len(generated_text))
		self.stats.token_count.add(token_count)
		self.stats.chars_per_second.add(len(generated_text) / duration_seconds)
		self.stats.tokens_per_second.add(token_count / duration_seconds)
		self.stats.print()
		return generated_text

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

def nvidia_smi():
	# Print nvidia-smi output
	print("nvidia-smi output:")
	print(subprocess.check_output(["nvidia-smi"]).decode())
	
nvidia_smi()
	
# Use the classes
print("Start Loading...", datetime.now())
llm = OpenAssistantLLM(model_name)
llm.start()
print("Done Loading!", datetime.now())

nvidia_smi()

def generate_text(user_prompt: str):
	print("Prompting...\n\n\n\n\n")
	prompt_generator = OpenAssistantPromptGenerator(SYSTEM_MESSAGE)
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