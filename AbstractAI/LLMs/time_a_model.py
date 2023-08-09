import argparse
from AbstractAI.Helpers.nvidia_smi import nvidia_smi
from AbstractAI.LLMs.LoadLLM import *

# Parse command-line arguments
parser = argparse.ArgumentParser(description='Process some integers.')
parser.add_argument('--model_name', type=str, default="OpenAssistant/falcon-7b-sft-mix-2000",
					help='The model name to use')
parser.add_argument('--system_message', type=str, default="You are a helpful assistant.",
					help='A pre message before all prompts that gets the model into the right frame of mind')
args = parser.parse_args()

# Extract the args
model_name = args.model_name
system_message = args.system_message

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

nvidia_smi()
	
# Use the classes
print("Start Loading...", datetime.now())
llm, prompt_generator = LoadLLM(model_name, system_message)
llm.start()
print("Done Loading!", datetime.now())

nvidia_smi()

def generate_text(user_prompt: str):
	print("Prompting...\n\n\n\n\n")
	prompt_generator.reset()
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