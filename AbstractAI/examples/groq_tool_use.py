from AbstractAI.Model.Settings.LLMSettings import LLMSettings
from AbstractAI.Model.Settings.Groq_LLMSettings import Groq_LLMSettings
from AbstractAI.Model.Converse import Conversation, Message, Role, UserSource, ConversationCollection, DATA
from AbstractAI.Tool import Tool
from ClassyFlaskDB.new.SQLStorageEngine import SQLStorageEngine
from typing import List, Dict
import os

# Function to get user's name
def get_user_name() -> str:
	'''
	This function will return my name.
	'''
	return "Charlie"

# Function to get current date and time
def get_current_datetime() -> str:
	'''
	This function will tell you what date and time it is.
	'''
	from datetime import datetime
	return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# Create Tool instances
name_tool = Tool.from_function(get_user_name)
datetime_tool = Tool.from_function(get_current_datetime)
tools = [name_tool, datetime_tool]

# Initialize the database
engine = SQLStorageEngine(f"sqlite:///new_engine_test1.db", DATA)

# Load LLM settings
groq_settings = next(engine.query(Groq_LLMSettings).all(where="user_model_name = 'llama ToolUser'"))

if groq_settings is None:
	print("Groq settings not found in the database.")
	exit(1)

# Load the LLM
llm = groq_settings.load()
llm.start()

# Create a new conversation
conversation = Conversation("Test Conversation", "A test conversation with Groq LLM")

# Add a user message
user = UserSource(user_name="User")
user_message = Message("Hello computer, what is my name?", Role.User())
user_message.source = user
conversation.add_message(user_message)

# Generate AI response
response = llm.chat(conversation, tools=tools)
conversation.add_message(response)
if llm.there_is_tool_call(response):
	print("There is tools!")
	conversation.add_messages(
		llm.call_tools(response, tools=tools)
	)
	response = llm.chat(conversation, tools=tools)
	conversation.add_message(response)
# Print the response
print("AI Response:")
print(response.content)

# Add another user message
user_message = Message("What date and time is it?", Role.User())
user_message.source = user
conversation.add_message(user_message)

# Generate another AI response
response = llm.chat(conversation, tools=tools)
conversation.add_message(response)
if llm.there_is_tool_call(response):
	print("There is tools!")
	conversation.add_messages(
		llm.call_tools(response, tools=tools)
	)
	response = llm.chat(conversation, tools=tools)
	conversation.add_message(response)

# Print the response
print("AI Response:")
print(response.content)

# Save the conversation to the database
conversation_collection = ConversationCollection.all_from_engine(engine)
conversation_collection.append(conversation)
engine.merge(conversation)

print("Conversation saved to the database.")