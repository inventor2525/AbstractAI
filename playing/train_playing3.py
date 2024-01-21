from datasets import Dataset
from transformers import AutoTokenizer, AutoModelForCausalLM

from transformers import TrainingArguments
from trl import SFTTrainer
from peft import get_peft_model, LoraConfig, prepare_model_for_int8_training
import torch


import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="torch.utils.checkpoint")

from auto_gptq import exllama_set_max_input_length
def gen_up_down(s):
    return f"__UP__{s}__DOWN__"#f"Counting UP:{s} Then counting down from 1 more than that:"

import warnings

# Suppress specific UserWarning from torch.utils.checkpoint
warnings.filterwarnings("ignore", category=UserWarning, module="torch.utils.checkpoint")

# Your dataset
dataset = [
    {"text": gen_up_down("1,2,3,4"),"label": "5,4,3,2,1"},
    {"text": gen_up_down("2,3,4,5"),"label": "6,5,4,3,2,1"},
    {"text": gen_up_down("3,4,5,6"),"label": "7,6,5,4,3,2,1"},
    {"text": gen_up_down("4,5,6,7"),"label": "8,7,6,5,4,3,2,1"},
    {"text": gen_up_down("5,6,7,8"),"label": "9,8,7,6,5,4,3,2,1"},
    {"text": gen_up_down("6,7,8,9"),"label": "10,9,8,7,6,5,4,3,2,1"},
	{"text": gen_up_down("7,8,9,10"),"label": "11,10,9,8,7,6,5,4,3,2,1"},
	{"text": gen_up_down("8,9,10,11"),"label": "12,11,10,9,8,7,6,5,4,3,2,1"},
]
import random

# dataset = []

# Parameters for the dataset
num_sequences = 30  # Number of sequences to generate
min_start_num = 1     # Minimum starting number
max_start_num = 300    # Maximum starting number
min_length = 2        # Minimum length of the sequence
max_length = 20       # Maximum length of the sequence

for _ in range(num_sequences):
    # Randomly choose a starting number and sequence length
    start_num = random.randint(min_start_num, max_start_num)
    length = random.randint(min_length, max_length)

    # Calculate end number for the up-counting sequence
    end_num = start_num + length - 1

    # Generate up-counting sequence (e.g., "2,3,4")
    up_sequence = ','.join(str(n) for n in range(start_num, end_num + 1))

    # Generate down-counting sequence (e.g., ",5,4,3,2,1")
    down_sequence = ','.join(str(n) for n in range(end_num + 1, 0, -1))

    # Combine sequences with 'f' prefix and 'd' suffix
    text = gen_up_down(up_sequence)
    label = f"{down_sequence}"

    # Add to dataset
    dataset.append({"text": text, "label": label})
    
# Convert to Hugging Face Dataset
hf_dataset = Dataset.from_dict({"text": [x["text"] + x["label"] for x in dataset]})

# Tokenizer
model_id = "TheBloke/TinyLlama-1.1B-python-v0.1-GPTQ"
model_id = "TinyLlama/TinyLlama-1.1B-python-v0.1"
model_id = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
model_id = "meta-llama/Llama-2-7b-hf"
# model_id = "TheBloke/Mistral-7B-v0.1-GPTQ"
# model_id = "TheBloke/Llama-2-7B-GPTQ"
# model_id = "TheBloke/Mixtral-8x7B-v0.1-GPTQ"
tokenizer = AutoTokenizer.from_pretrained(model_id, use_fast=True)
# tokenizer.pad_token_id = 0
tokenizer.pad_token = tokenizer.eos_token



tokenizer.padding_side = 'right'

# Preprocess function
def preprocess_function(examples):
    return tokenizer(examples["text"], padding="max_length", truncation=True, max_length=256, add_special_tokens=False)

# Tokenize the dataset
tokenized_dataset = hf_dataset.map(preprocess_function, batched=True)

# Load Model
model = AutoModelForCausalLM.from_pretrained(model_id, device_map="auto", trust_remote_code=True)
# model = exllama_set_max_input_length(model, 4000)

# Function to generate text using the model
def generate_text(prompt, model):
	inputs = tokenizer(prompt, return_tensors="pt", add_special_tokens=False, max_length=256)
	inputs = inputs.to(model.device)
	outputs = model.generate(**inputs, do_sample=True, top_p=0.95, top_k=0, max_new_tokens=50, forced_bos_token_id=None, bos_token_id=None)
	return tokenizer.decode(outputs[0], add_special_tokens=False, max_length=256)

def generate_and_print(prompt, model):
	generated_text = generate_text(prompt, model)
	print("Input:", prompt)
	print("Generated continuation:", generated_text)


generate_and_print(gen_up_down("1,2,3,4,5,6,7,8,9,10,11,12,13,14,15"), model)
generate_and_print(gen_up_down("1,2,3"), model)
generate_and_print(gen_up_down("6,7,8,9"), model)
generate_and_print(gen_up_down("128,129,130"), model)

# Define training arguments
training_args = TrainingArguments(
    output_dir="./model_output",
    num_train_epochs=1,
    per_device_train_batch_size=8,
    # Include other training arguments as needed
)

# # print(model)
# model = prepare_model_for_int8_training(model)
# config = LoraConfig(
#     r=64,
#     lora_alpha=16,
#     target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
#                       "gate_proj", "up_proj", "down_proj",],
#     lora_dropout=0.1,
#     bias="none",
#     task_type="CAUSAL_LM",
# )

# # print(model)
# # After applying LoRA
# model = get_peft_model(model, config)

# # Check if the LoRA parameters have requires_grad=True
# for name, param in model.named_parameters():
#     if "lora" in name:
#         print(f"{name} - requires_grad: {param.requires_grad}")

# # Check if there are any trainable parameters in the model
# trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
# print(f"Number of trainable parameters: {trainable_params}")

# Create SFT Trainer instance
trainer = SFTTrainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_dataset,
    tokenizer=tokenizer,
    dataset_text_field="text",
    max_seq_length=256,
)

# Train the model
trainer.train()

# Save the model and tokenizer
model.save_pretrained('./my_fine_tuned_model')
tokenizer.save_pretrained('./my_fine_tuned_model')

generate_and_print(gen_up_down("1,2,3,4,5,6,7,8,9,10,11,12,13,14,15"), trainer.model)
generate_and_print(gen_up_down("1,2,3"), trainer.model)
generate_and_print(gen_up_down("6,7,8,9"), trainer.model)
generate_and_print(gen_up_down("128,129,130"), trainer.model)