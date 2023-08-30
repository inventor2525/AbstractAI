import openai
from AbstractAI.LLMs.OpenAI_LLM import OpenAI_LLM
from AbstractAI.Conversation import Conversation, Message, Role
import unittest

run_tests = True

class TestLLM(unittest.TestCase):
	def test_openai_llm_conversation(self):
		if run_tests:
			llm = OpenAI_LLM()

			# Create a conversation
			conversation = Conversation()
			conversation.add_message(Message("You are a chat bot.", Role.System))
			conversation.add_message(Message("Write me a python script to count to 5.", Role.User))

			response = llm.prompt(conversation)
			conversation.add_message(response.message)
			self.assertEqual(len(conversation.message_sequence.messages), 3)
			self.assertGreater(len(response.message.content), 0)

			# Add another user message
			conversation.add_message(Message("Not like that.", Role.User))

			# Prompt the model again
			response = llm.prompt(conversation)
			conversation.add_message(response.message)
			self.assertEqual(len(conversation.message_sequence.messages), 5)
			self.assertGreater(len(response.message.content), 0)

			# Print the conversation messages
			for message in conversation.message_sequence.messages:
				print(f"{message.role}: {message.content}")

if __name__ == '__main__' and run_tests:
	unittest.main()