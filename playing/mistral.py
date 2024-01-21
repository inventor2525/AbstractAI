from typing import List, Optional
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline

model_name_or_path = "TheBloke/Mistral-7B-Instruct-v0.2-GPTQ"
# # To use a different branch, change revision
# # For example: revision="gptq-4bit-32g-actorder_True"
# model = AutoModelForCausalLM.from_pretrained(model_name_or_path,
#                                              device_map="auto",
#                                              trust_remote_code=False,
#                                              revision="gptq-8bit-32g-actorder_True")
from transformers import MistralForCausalLM

class ModifiedMistralForCausalLM(MistralForCausalLM):
    def forward(
        self,
        input_ids: torch.LongTensor = None,
        attention_mask: Optional[torch.Tensor] = None,
        position_ids: Optional[torch.LongTensor] = None,
        past_key_values: Optional[List[torch.FloatTensor]] = None,
        inputs_embeds: Optional[torch.FloatTensor] = None,
        use_cache: Optional[bool] = None,
        output_attentions: Optional[bool] = None,
        output_hidden_states: Optional[bool] = None,
        return_dict: Optional[bool] = None,
    ):
        # Call the original forward method of the MistralModel with accepted arguments
        outputs = self.model(
            input_ids=input_ids,
            attention_mask=attention_mask,
            position_ids=position_ids,
            past_key_values=past_key_values,
            inputs_embeds=inputs_embeds,
            use_cache=use_cache,
            output_attentions=output_attentions,
            output_hidden_states=output_hidden_states,
            return_dict=return_dict,
        )

        # Get the last hidden states (the logits before they are passed through lm_head)
        hidden_states = outputs[0]

        # Return the hidden states instead of logits
        return hidden_states

# Now instantiate your modified model
model = ModifiedMistralForCausalLM.from_pretrained(model_name_or_path,
                                                   device_map="auto",
                                                   trust_remote_code=False,
                                                   revision="gptq-8bit-32g-actorder_True")

tokenizer = AutoTokenizer.from_pretrained(model_name_or_path, use_fast=True)

# Example usage
inputs = tokenizer("Your input text", return_tensors="pt")
hidden_states = model(**inputs)

# If you need probabilities, apply softmax to hidden states
import torch.nn.functional as F
probabilities = F.softmax(hidden_states.to(torch.float32), dim=-1)
print("hello")