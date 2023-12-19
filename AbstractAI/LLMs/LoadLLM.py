from .OpenAssistant import *
from .StableBeluga2 import *
from .Mistral import *
from typing import Tuple

def LoadLLM(model_name: str) -> LLM:
	print(f"Loading LLM '{model_name}'...")
	llm = None
	if model_name.startswith("OpenAssistant"):
		llm = OpenAssistantLLM(model_name)
	if model_name.startswith("stabilityai/StableBeluga"):
		llm = StableBeluga2(model_name)
	if model_name == "Mistral":
		llm = Mistral()
	print(llm)
	return llm