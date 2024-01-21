import torch
from transformers import MistralForCausalLM, AutoTokenizer, AutoModelForCausalLM
import torch.nn.functional as F
from typing import List, Optional, Set
import math

class ConstrainedGenerator:
    def __init__(self):
        # Hardcoded model and tokenizer initialization with specific parameters
        model_name_or_path = ["TheBloke/Mistral-7B-Instruct-v0.2-GPTQ", "gptq-8bit-32g-actorder_True"]
        #model_name_or_path = ["TheBloke/Mixtral-8x7B-v0.1-GPTQ", "gptq-4bit-32g-actorder_True"]
        self.tokenizer = AutoTokenizer.from_pretrained(model_name_or_path[0], use_fast=True)
        self.model = AutoModelForCausalLM.from_pretrained(model_name_or_path[0], 
                                                        revision=model_name_or_path[1],
                                                        device_map="auto", 
                                                        trust_remote_code=False)
        self.model.eval()  # Set the model to evaluation mode

    def generate(self, prompt: str, possible_outputs: [str]) -> str:
        # Tokenize the prompt
        input_ids = self.tokenizer(prompt, return_tensors="pt").input_ids
        current_output_ids = torch.tensor([], dtype=torch.long).to(input_ids.device)

        while True:
            # Decode the generated token ids to a string
            current_output = self.tokenizer.decode(current_output_ids, skip_special_tokens=True)

            # Determine the next possible tokens based on current output
            next_possible_tokens = set()
            for possible_output in possible_outputs:
                possible_output_ids = self.tokenizer.encode(possible_output, add_special_tokens=False)
                if current_output_ids.tolist() == possible_output_ids[:len(current_output_ids)]:
                    if len(current_output_ids) < len(possible_output_ids):
                        next_possible_tokens.add(possible_output_ids[len(current_output_ids)])

            # Break the loop if there are no possible next tokens
            if len(next_possible_tokens) == 0:
                break

            # If there is only one possible next token, add it directly without calling the model
            if len(next_possible_tokens) == 1:
                next_token_id = next_possible_tokens.pop()
                current_output_ids = torch.cat([current_output_ids, torch.tensor([next_token_id], device=input_ids.device)])
                continue

            # If multiple possible next tokens, use the model to predict the next token
            with torch.no_grad():
                concatenated_ids = torch.cat([input_ids, current_output_ids.unsqueeze(0)], dim=1)
                outputs = self.model(concatenated_ids)
                logits = outputs.logits

            next_token_logits = logits[0, -1, :]
            mask = torch.full((self.model.config.vocab_size,), -float('inf'), device=input_ids.device)
            mask[list(next_possible_tokens)] = 0  # Set allowed tokens to 0, rest remain -inf
            masked_logits = next_token_logits + mask  # Add mask to logits
            next_token_id = torch.argmax(F.softmax(masked_logits, dim=-1))

            # Append the selected token id to the current output ids
            current_output_ids = torch.cat([current_output_ids, next_token_id.unsqueeze(0)])

        # Decode the final output ids to a string and return
        return self.tokenizer.decode(current_output_ids, skip_special_tokens=True)

# Example usage of the class is omitted as per your request

# Example usage
generator = ConstrainedGenerator()
print(generator.generate("Example prompt text", ["Option 2", "Option 1", "Option 3"]))
print(generator.generate("I like ", ["Potatos", "Carrots", "Kitens", "Horses", "Beavers"]))
