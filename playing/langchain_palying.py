from langchain_community.llms.huggingface_pipeline import HuggingFacePipeline
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
from langchain.prompts import PromptTemplate

template = """Question: {question}

Answer: Let's think step by step."""
prompt = PromptTemplate.from_template(template)

model_id = "TheBloke/Mixtral-8x7B-v0.1-GPTQ"
tokenizer = AutoTokenizer.from_pretrained(model_id, use_fast=True)
model = AutoModelForCausalLM.from_pretrained(model_id, device_map="auto", trust_remote_code=False)
pipe = pipeline("text-generation", model=model, tokenizer=tokenizer, max_new_tokens=200)
hf = HuggingFacePipeline(pipeline=pipe)

# gpu_llm = HuggingFacePipeline.from_model_id(
#     model_id=model_id,
#     task="text-generation",
#     device_map="auto",  # replace with device_map="auto" to use the accelerate library.
#     pipeline_kwargs={"max_new_tokens": 10},
# )

gpu_chain = prompt | hf

question = "What is electroencephalography?"

print(gpu_chain.invoke({"question": question}))