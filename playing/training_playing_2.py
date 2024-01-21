from datasets import Dataset
from transformers import AutoTokenizer, AutoModelForCausalLM

from transformers import TrainingArguments
from trl import SFTTrainer
import torch

# Your dataset
dataset = [
    {"text": "1, 2, 3, 4", "label": ", 5"},
    {"text": "2, 3, 4, 5", "label": ", 6"},
    {"text": "3, 4, 5, 6", "label": ", 7"},
    {"text": "4, 5, 6, 7", "label": ", 8"},
    {"text": "5, 6, 7, 8", "label": ", 9"}
]

# Convert to Hugging Face Dataset
hf_dataset = Dataset.from_dict({"text": [x["text"] + x["label"] for x in dataset]})

# Tokenizer
model_id = "gpt2"# "TheBloke/Mixtral-8x7B-v0.1-GPTQ"
tokenizer = AutoTokenizer.from_pretrained(model_id, use_fast=True)
tokenizer.pad_token = tokenizer.eos_token
tokenizer.padding_side = 'right'

# Preprocess function
def preprocess_function(examples):
    return tokenizer(examples["text"], padding="max_length", truncation=True, max_length=512)

# Tokenize the dataset
tokenized_dataset = hf_dataset.map(preprocess_function, batched=True)

# Load Model
model = AutoModelForCausalLM.from_pretrained(model_id, device_map="auto")

# Define training arguments
training_args = TrainingArguments(
    output_dir="./model_output",
    num_train_epochs=3,
    per_device_train_batch_size=8,
    
    # Include other training arguments as needed
)

# Create SFT Trainer instance
trainer = SFTTrainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_dataset,
    tokenizer=tokenizer,
    
    dataset_text_field="text"
)

# Train the model
trainer.train()

# Save the model and tokenizer
model.save_pretrained('./my_fine_tuned_model')
tokenizer.save_pretrained('./my_fine_tuned_model')
