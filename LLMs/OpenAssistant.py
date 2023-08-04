#modified from from https://huggingface.co/OpenAssistant/llama2-13b-orca-v2-8k-3166 & https://huggingface.co/OpenAssistant/llama2-13b-orca-8k-3319
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from datetime import datetime

# Define common strings
SYSTEM_MESSAGE = "You are a helpful assistant."

# Set model
model_name = "OpenAssistant/llama2-13b-orca-v2-8k-3166"
model_name = "OpenAssistant/falcon-40b-sft-mix-1226"
model_name = "OpenAssistant/falcon-40b-sft-top1-560"
model_name = "OpenAssistant/falcon-7b-sft-mix-2000"

# Define base classes
class LLM:
	def __init__(self):
		self.model = None
		self.tokenizer = None

	def start(self):
		raise NotImplementedError

	def respond(self, prompt):
		inputs = self.tokenizer(prompt, return_tensors="pt").to("cuda")
		output = self.model.generate(**inputs, do_sample=True, top_p=0.95, top_k=0, max_new_tokens=1024)
		return output

	def timed_prompt(self, prompt):
		start_time = datetime.now()
		output = self.respond(prompt)
		end_time = datetime.now()
		generated_text = self.tokenizer.decode(output[0], skip_special_tokens=True)
		duration = end_time - start_time
		duration_seconds = duration.total_seconds()
		token_count = len(output[0])
		chars_per_second = len(generated_text) / duration_seconds
		tokens_per_second = token_count / duration_seconds
		print(f"Start time: {start_time}")
		print(f"End time: {end_time}")
		print(f"Duration: {duration_seconds} seconds")
		print(f"Response length: {len(generated_text)} characters")
		print(f"Token count: {token_count}")
		print(f"Characters per second: {chars_per_second}")
		print(f"Tokens per second: {tokens_per_second}")
		return generated_text

class OpenAssistantLLM(LLM):
	def __init__(self, model_name):
		super().__init__()
		self.model_name = model_name

	def start(self):
		self.tokenizer = AutoTokenizer.from_pretrained(self.model_name, use_fast=False)
		self.model = AutoModelForCausalLM.from_pretrained(self.model_name, torch_dtype=torch.float16, low_cpu_mem_usage=True, device_map="auto")

class PromptGenerator:
	def __init__(self, system_message):
		self.system_message = system_message
		self.conversation = ""

	def add_prompt(self, user_prompt):
		raise NotImplementedError

	def add_response(self, ai_response):
		raise NotImplementedError
	
	def get_prompt(self):
		return self.conversation

class OpenAssistantPromptGenerator(PromptGenerator):
	def __init__(self, system_message):
		super(PromptGenerator, obj)
		self.conversation = f"""<|system|>{self.system_message}</s>"""
		
	def add_prompt(self, user_prompt):
		self.conversation += f"<|prompter|>{user_prompt}</s>"

	def add_response(self, ai_response):
		self.conversation += f"<|assistant|>{ai_response}</s>"
	
	def get_prompt(self):
		return f"{self.conversation}<|assistant|>"

# Use the classes
print("Start...", datetime.now())
llm = OpenAssistantLLM(model_name)
llm.start()
print("done loading!", datetime.now())

def generate_text(user_prompt):
	prompt_generator = OpenAssistantPromptGenerator(SYSTEM_MESSAGE)
	prompt_generator.add_prompt(user_prompt)
	
	response = llm.timed_prompt(prompt_generator.get_prompt())
	
	prompt_generator.add_response(response)
	print(prompt_generator.conversation)

# Call the function for different prompts
generate_text("Write me a poem please")
generate_text("Write me a vector3 class in python with lots of useful math functions")
generate_text("Write me a python quaternion class with lots of useful math functions.")
generate_text("Write me a vhdl binary counter")
generate_text("Write me a vhdl 4 pin stepper motor controller.")