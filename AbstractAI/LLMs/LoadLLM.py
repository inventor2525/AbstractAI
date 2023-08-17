from .OpenAssistant import *
from .StableBeluga2 import *
from typing import Tuple

from .Conversation import Conversation

def LoadLLM(model_name: str, system_message: str) -> LLM:
	print(f"Loading LLM '{model_name}' with system message '{system_message}'")
	llm = None
	if model_name.startswith("OpenAssistant"):
		llm = OpenAssistantLLM(model_name)
	if model_name.startswith("stabilityai/StableBeluga"):
		llm = StableBeluga2(model_name)
	print(llm)
	return llm