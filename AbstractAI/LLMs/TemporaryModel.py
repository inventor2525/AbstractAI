from llama_cpp import Llama
model_path = '/home/charlie/Projects/text-generation-webui/models/mixtral-8x7b-instruct-v0.1.Q4_K_M.gguf'
#model_path = './text-generation-webui/models/mistral-7b-instruct-v0.1.Q5_K_S.gguf'
# Set gpu_layers to the number of layers to offload to GPU. Set to 0 if no GPU acceleration is available on your system.
llm = Llama(
  model_path=model_path,  # Download the model file first
  n_ctx=2048,  # The max sequence length to use - note that longer sequence lengths require much more resources
  n_threads=7,            # The number of CPU threads to use, tailor to your system and the resulting performance
  n_gpu_layers=0         # The number of layers to offload to GPU, if you have GPU acceleration available
)

def prompt(prompt):
  output = llm(
    f"[INST] {prompt} [/INST]", # Prompt
    max_tokens=512,  # Generate up to 512 tokens
    stop=["</s>"],   # Example stop token - not necessarily correct for this specific model! Please check before using.
    echo=False        # Whether to echo the prompt
  )
  return output['choices'][0]['text']