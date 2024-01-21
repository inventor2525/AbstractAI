from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from peft import LoraConfig, TaskType, get_peft_model, prepare_model_for_kbit_training
from datasets import Dataset
from transformers import AutoTokenizer, AutoModelForCausalLM
from transformers import TrainingArguments, TrainerCallback
from trl import SFTTrainer
from peft import get_peft_model, LoraConfig, prepare_model_for_int8_training, LoftQConfig
import torch
import mlflow


import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="torch.utils.checkpoint")
import torch
from auto_gptq import exllama_set_max_input_length
def gen_up_down(s):
	return f"__UP__{s}__DOWN__"

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
# Create quantization config
quantization_config = BitsAndBytesConfig(
	load_in_4bit=True,
	bnb_4bit_use_double_quant=True,
	bnb_4bit_compute_dtype=torch.float16,
	bnb_4bit_quant_type="nf4"
)
model_id = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
model_id = "meta-llama/Llama-2-7b-hf"
model_id = "mistralai/Mixtral-8x7B-v0.1"
model_id = "mistralai/Mixtral-8x7B-Instruct-v0.1"
tokenizer = AutoTokenizer.from_pretrained(model_id, use_fast=True)
# tokenizer.pad_token_id = 0
tokenizer.pad_token = tokenizer.eos_token
tokenizer.padding_side = 'right'
# Base model
model = AutoModelForCausalLM.from_pretrained(model_id,
											 quantization_config=quantization_config,
											 device_map="auto",
											 )

# Prepare quantized model for peft training
model = prepare_model_for_kbit_training(model)

# Create peft config
lora_config = LoraConfig(
	r=128,
	target_modules=["q_proj", "o_proj", "k_proj", "v_proj", "gate_proj", "up_proj", "down_proj"],
	bias="none",
	task_type=TaskType.CAUSAL_LM,
	lora_alpha=16,
)

# Create PeftModel which inserts LoRA adapters using the above config
model = get_peft_model(model, lora_config)

# Train the model using HF Trainer/ HF Accelerate/ custom loop









def get_data_set(num_sequences=200, min_start_num=1, max_start_num=300, min_length=2, max_length=20):
	dataset = []

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

	# Preprocess function
	def preprocess_function(examples):
		return tokenizer(examples["text"], padding="max_length", truncation=True, max_length=256, add_special_tokens=False)

	# Tokenize the dataset
	return hf_dataset.map(preprocess_function, batched=True)

# Function to generate text using the model
def generate_text(prompt, model):
	inputs = tokenizer(prompt, return_tensors="pt", add_special_tokens=False, max_length=256)
	inputs = inputs.to(model.device)
	outputs = model.generate(**inputs, do_sample=True, top_p=0.95, top_k=0, max_new_tokens=50, forced_bos_token_id=None, bos_token_id=None)
	return tokenizer.decode(outputs[0], add_special_tokens=False, max_length=256)

def generate_and_print(prompt, model):
	generated_text = generate_text(prompt, model)
	# print("Input:", prompt)
	print("\nGenerated continuation:", generated_text)

generate_and_print(gen_up_down("1,2,3,4,5,6,7,8,9,10,11,12,13,14,15"), model)
generate_and_print(gen_up_down("1,2,3"), model)
generate_and_print(gen_up_down("6,7,8,9"), model)
generate_and_print(gen_up_down("128,129,130"), model)

trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
print(f"Number of trainable parameters: {trainable_params}")

class MLflowLoggingCallback(TrainerCallback):
	def on_log(self, args, state, control, logs=None, **kwargs):
		# Log metrics to MLflowf
		if logs is not None:
			for key, value in logs.items():
				if key in ["loss", "eval_loss"]:
					mlflow.log_metric(key, value, step=state.global_step)

	def on_evaluate(self, args, state, control, metrics=None, **kwargs):
		# Log evaluation metrics
		if metrics is not None:
			for key, value in metrics.items():
				if key in ["eval_loss"]:
					mlflow.log_metric(key, value, step=state.global_step)

# Define training arguments
training_args = TrainingArguments(
	output_dir="./model_output",
	num_train_epochs=1,
	per_device_train_batch_size=8,
	evaluation_strategy="steps",
	logging_steps=10,
	learning_rate=0.0001,
)

# Create SFT Trainer instance
trainer = SFTTrainer(
	model=model,
	args=training_args,
	train_dataset=get_data_set(1000),
	eval_dataset=get_data_set(10),
	tokenizer=tokenizer,
	dataset_text_field="text",
	callbacks=[MLflowLoggingCallback()],
	max_seq_length=256,
)

with mlflow.start_run():
	# Train the model
	trainer.train()

generate_and_print(gen_up_down("1,2,3,4,5,6,7,8,9,10,11,12,13,14,15"), model)
generate_and_print(gen_up_down("1,2,3"), model)
generate_and_print(gen_up_down("6,7,8,9"), model)
generate_and_print(gen_up_down("128,129,130"), model)

# Save the adapter weights
model.save_pretrained("my_awesome_adapter")
