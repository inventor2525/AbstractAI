from transformers import MistralForCausalLM, AutoTokenizer
import torch

# Load the model and tokenizer
model_name_or_path = "TheBloke/Mistral-7B-Instruct-v0.2-GPTQ"
model = MistralForCausalLM.from_pretrained(model_name_or_path)
tokenizer = AutoTokenizer.from_pretrained(model_name_or_path, use_fast=True)

# Set the model to evaluation mode
model.eval()

# Example input
input_text = "Example input text"
input_ids = tokenizer(input_text, return_tensors="pt").input_ids

# Forward pass to get logits
with torch.no_grad():
    outputs = model(input_ids)
    logits = outputs.logits  # Accessing logits directly

# The `logits` tensor now contains the raw output of the transformer layers
print("hello")