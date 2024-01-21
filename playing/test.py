from transformers import GPT2LMHeadModel, GPT2Tokenizer
from langchain.agents import tool, AgentExecutor

# Step 1: Load the language model
model_name = "gpt2"
model = GPT2LMHeadModel.from_pretrained(model_name)
tokenizer = GPT2Tokenizer.from_pretrained(model_name)

# Step 2: Define a custom tool
@tool
def custom_tool(input_text: str) -> str:
    # Perform some processing using the Hugging Face model
    encoded_input = tokenizer.encode(input_text, return_tensors="pt")
    output = model.generate(encoded_input)
    decoded_output = tokenizer.decode(output[0], skip_special_tokens=True)
    return decoded_output

# Step 3: Create a list of tools
tools = [custom_tool]

# Step 4: Define the agent
agent = {
    "input": lambda x: x["input"],
    "tool_input": lambda x: x["tool_input"],
} | custom_tool

# Step 5: Create an instance of AgentExecutor
agent_executor = AgentExecutor(agent=agent, tools=tools)

# Step 6: Invoke the agent
input_data = {
    "input": "Hello",
    "tool_input": "Some input for the custom tool",
}
output = agent_executor.invoke(input_data)
print(output)