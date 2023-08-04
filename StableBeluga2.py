#copied from https://huggingface.co/spaces/Sentdex/StableBeluga2-70B-Chat/tree/main
import gradio as gr
import transformers
from torch import bfloat16
# from dotenv import load_dotenv  # if you wanted to adapt this for a repo that uses auth
from threading import Thread


#HF_AUTH = os.getenv('HF_AUTH')
model_id = "stabilityai/StableBeluga2" # 70B parm model based off Llama 2 70B

bnb_config = transformers.BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type='nf4',
    bnb_4bit_use_double_quant=True,
    bnb_4bit_compute_dtype=bfloat16
)
model_config = transformers.AutoConfig.from_pretrained(
    model_id,
    #use_auth_token=HF_AUTH
)

model = transformers.AutoModelForCausalLM.from_pretrained(
    model_id,
    trust_remote_code=True,
    config=model_config,
    quantization_config=bnb_config,
    device_map='auto',
    #use_auth_token=HF_AUTH
)

tokenizer = transformers.AutoTokenizer.from_pretrained(
    model_id,
    #use_auth_token=HF_AUTH
)

DESCRIPTION = """
# StableBeluga2 70B Chat
This is a streaming Chat Interface implementation of [StableBeluga2](https://huggingface.co/stabilityai/StableBeluga2) 
You can modify the system prompt, which can be quite fun. For example, you can try something like "You are a mean AI. Phrase all replies as insults" for a good laugh.

Sometimes the model doesn't appropriately hit its stop token. Feel free to hit "stop" and "retry" if this happens to you. Or PR a fix to stop the stream if the tokens for User: get hit or something.
"""

def prompt_build(system_prompt, user_inp, hist):
    prompt = f"""### System:\n{system_prompt}\n\n"""
    
    for pair in hist:
        prompt += f"""### User:\n{pair[0]}\n\n### Assistant:\n{pair[1]}\n\n"""

    prompt += f"""### User:\n{user_inp}\n\n### Assistant:"""
    return prompt

def chat(user_input, history, system_prompt):

    prompt = prompt_build(system_prompt, user_input, history)
    model_inputs = tokenizer([prompt], return_tensors="pt").to("cuda")

    streamer = transformers.TextIteratorStreamer(tokenizer, timeout=10., skip_prompt=True, skip_special_tokens=True)

    generate_kwargs = dict(
        model_inputs,
        streamer=streamer,
        max_new_tokens=2048,
        do_sample=True,
        top_p=0.95,
        temperature=0.8,
        top_k=50
    )
    t = Thread(target=model.generate, kwargs=generate_kwargs)
    t.start()

    model_output = ""
    for new_text in streamer:
        model_output += new_text
        yield model_output
    return model_output


with gr.Blocks() as demo:
    gr.Markdown(DESCRIPTION)
    system_prompt = gr.Textbox("You are helpful AI.", label="System Prompt")
    chatbot = gr.ChatInterface(fn=chat, additional_inputs=[system_prompt])

demo.queue().launch()