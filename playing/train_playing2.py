from datasets import Dataset
from transformers import AutoTokenizer, AutoModelForCausalLM
from transformers import TrainingArguments, TrainerCallback
from trl import SFTTrainer
from peft import get_peft_model, LoraConfig, prepare_model_for_int8_training, LoftQConfig, prepare_model_for_kbit_training
import torch
import mlflow

import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="torch.utils.checkpoint")

from auto_gptq import exllama_set_max_input_length
def gen_up_down(s):
    return f"Counting UP:{s} Then counting down from 1 more than that:"

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

model_id = "TheBloke/TinyLlama-1.1B-python-v0.1-GPTQ"
model_id = "TheBloke/Mistral-7B-v0.1-GPTQ"
model_id = "TheBloke/TinyLlama-1.1B-Chat-v1.0-GPTQ"
# model_id = "TheBloke/Llama-2-7B-GPTQ"
# model_id = "TheBloke/Mixtral-8x7B-v0.1-GPTQ"
tokenizer = AutoTokenizer.from_pretrained(model_id, use_fast=True)
# tokenizer.pad_token_id = 0
tokenizer.pad_token = tokenizer.eos_token
tokenizer.padding_side = 'right'

# Load Model
model = AutoModelForCausalLM.from_pretrained(model_id, device_map="auto")
model = exllama_set_max_input_length(model, 4000)

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
    evaluation_strategy="steps",
    logging_steps=10,
    learning_rate=0.00002,
)

# print(model)
model = prepare_model_for_kbit_training(model)
config = LoraConfig(
    r=128,
    lora_alpha=18,#o_proj
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
    lora_dropout=0.1,
    bias="lora_only",
    task_type="CAUSAL_LM"
)

# print(model)
# After applying LoRA
model = get_peft_model(model, config)

# # Check if the LoRA parameters have requires_grad=True
# for name, param in model.named_parameters():
#     if "lora" in name:
#         print(f"{name} - requires_grad: {param.requires_grad}")

# # Check if there are any trainable parameters in the model
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
# Create SFT Trainer instance
trainer = SFTTrainer(
    model=model,
    args=training_args,
    train_dataset=get_data_set(2000),
    eval_dataset=get_data_set(10),
    tokenizer=tokenizer,
    dataset_text_field="text",
    callbacks=[MLflowLoggingCallback()],
    max_seq_length=256,
)

with mlflow.start_run():
    # Train the model
    trainer.train()

# Save the model and tokenizer
model.save_pretrained('./my_fine_tuned_model')
tokenizer.save_pretrained('./my_fine_tuned_model')

generate_and_print(gen_up_down("1,2,3,4,5,6,7,8,9,10,11,12,13,14,15"), trainer.model)
generate_and_print(gen_up_down("1,2,3"), trainer.model)
generate_and_print(gen_up_down("6,7,8,9"), trainer.model)
generate_and_print(gen_up_down("128,129,130"), trainer.model)