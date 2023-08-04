#copied from https://huggingface.co/OpenAssistant/llama2-13b-orca-8k-3319
#better from https://huggingface.co/OpenAssistant/llama2-13b-orca-v2-8k-3166
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from datetime import datetime

print("Start...", datetime.now())
tokenizer = AutoTokenizer.from_pretrained("OpenAssistant/llama2-13b-orca-v2-8k-3166", use_fast=False)
model = AutoModelForCausalLM.from_pretrained("OpenAssistant/llama2-13b-orca-v2-8k-3166", torch_dtype=torch.float16, low_cpu_mem_usage=True, device_map="auto")
print("done loading!", datetime.now())

print("Run...", datetime.now())
system_message = "You are a helpful assistant."
user_prompt = "Write me a poem please"
prompt = f"""<|system|>{system_message}</s><|prompter|>{user_prompt}</s><|assistant|>"""
inputs = tokenizer(prompt, return_tensors="pt").to("cuda")
output = model.generate(**inputs, do_sample=True, top_p=0.95, top_k=0, max_new_tokens=256)
print(tokenizer.decode(output[0], skip_special_tokens=True))
print("done running", datetime.now())


print("Run...", datetime.now())
system_message = "You are a helpful assistant."
user_prompt = "Write me a vector3 class in python with lots of useful math functions"
prompt = f"""<|system|>{system_message}</s><|prompter|>{user_prompt}</s><|assistant|>"""
inputs = tokenizer(prompt, return_tensors="pt").to("cuda")
output = model.generate(**inputs, do_sample=True, top_p=0.95, top_k=0, max_new_tokens=256)
print(tokenizer.decode(output[0], skip_special_tokens=True))
print("done running", datetime.now())


print("Run...", datetime.now())
system_message = "You are a helpful assistant."
user_prompt = "Write me a python quaternion class with lots of useful math functions."
prompt = f"""<|system|>{system_message}</s><|prompter|>{user_prompt}</s><|assistant|>"""
inputs = tokenizer(prompt, return_tensors="pt").to("cuda")
output = model.generate(**inputs, do_sample=True, top_p=0.95, top_k=0, max_new_tokens=256)
print(tokenizer.decode(output[0], skip_special_tokens=True))
print("done running", datetime.now())

print("Run...", datetime.now())
system_message = "You are a helpful assistant."
user_prompt = "Write me a vhdl binary counter"
prompt = f"""<|system|>{system_message}</s><|prompter|>{user_prompt}</s><|assistant|>"""
inputs = tokenizer(prompt, return_tensors="pt").to("cuda")
output = model.generate(**inputs, do_sample=True, top_p=0.95, top_k=0, max_new_tokens=256)
print(tokenizer.decode(output[0], skip_special_tokens=True))
print("done running", datetime.now())

print("Run...", datetime.now())
system_message = "You are a helpful assistant."
user_prompt = "Write me a vhdl 4 pin stepper motor controller."
prompt = f"""<|system|>{system_message}</s><|prompter|>{user_prompt}</s><|assistant|>"""
inputs = tokenizer(prompt, return_tensors="pt").to("cuda")
output = model.generate(**inputs, do_sample=True, top_p=0.95, top_k=0, max_new_tokens=256)
print(tokenizer.decode(output[0], skip_special_tokens=True))
print("done running", datetime.now())