from AbstractAI.ChatBot import *
from AbstractAI.LLMs.OpenAI_LLM import *
from AbstractAI.DB.Database import *

db = Database("sqlite:///test.sql")
model = OpenAI_LLM()
bot = ChatBot(model, db)
bot.conversation.add_message(message=Message("You are an automated coding assistant, it is very important that you respond in a certain format so code can be copied to file automatically. Respond only with ```python ``` blocks.", Role.System, source=UserSource("System")))
while True:
	print(bot.prompt(input("> ")))