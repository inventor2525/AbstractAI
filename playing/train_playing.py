from datasets import Dataset
from transformers import AutoTokenizer, AutoModelForCausalLM, Trainer, TrainingArguments, DataCollatorWithPadding
import peft  # Ensure PEFT is installed

# Dataset
dataset = [
	{"text": "1, 2, 3, 4", "label": ", 5"},
	{"text": "2, 3, 4, 5", "label": ", 6"},
	{"text": "3, 4, 5, 6", "label": ", 7"},
	{"text": "4, 5, 6, 7", "label": ", 8"},
	{"text": "5, 6, 7, 8", "label": ", 9"}
]
from datasets import load_dataset
# print(load_dataset("yelp_review_full"))
# Tokenizer
model_id = "gpt2"#"TheBloke/Mixtral-8x7B-v0.1-GPTQ"
tokenizer = AutoTokenizer.from_pretrained(model_id, use_fast=True)
tokenizer.pad_token = tokenizer.eos_token

def preprocess_function(examples):
	# return tokenizer(examples["text"], padding="max_length", truncation=True)
	concatenated_texts = [t + l for t, l in zip(examples["text"], examples["label"])]
	return tokenizer(concatenated_texts, padding="max_length", truncation=True)


# Convert list of examples to Hugging Face Dataset
hf_dataset = load_dataset("yelp_review_full")# Dataset.from_list(dataset)
hf_dataset = Dataset.from_dict(hf_dataset["train"][0:100])
hf_dataset = Dataset.from_list(dataset)

# Tokenize the dataset
tokenized_dataset = hf_dataset.map(preprocess_function, batched=True)

# Load Model and Add Adapters
model = AutoModelForCausalLM.from_pretrained(model_id, device_map="auto")

# # Define and add a new adapter
# adapter_config = peft.LoraConfig(
	
#     lora_alpha=16,
#     lora_dropout=0.1,
#     r=64,
#     bias="none",
#     task_type="CAUSAL_LM",
#     # target_modules=["q_proj", "k_proj"],  # Specify target modules here
#     # Add other configuration settings as needed
# )
# model.add_adapter(adapter_config)

data_collator = DataCollatorWithPadding(tokenizer=tokenizer, return_tensors="pt")
# Training
training_args = TrainingArguments(
	output_dir="./model_output",
	num_train_epochs=3,
	per_device_train_batch_size=8
)
trainer = Trainer(
	model=model,
	args=training_args,
	train_dataset=tokenized_dataset,
	data_collator=data_collator,
	tokenizer=tokenizer,
)
trainer.train()

# Save the model
model.save_pretrained('./my_fine_tuned_model')
tokenizer.save_pretrained('./my_fine_tuned_model')

# For loading the model later
model = AutoModelForCausalLM.from_pretrained('./my_fine_tuned_model')
