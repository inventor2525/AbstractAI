from .OpenAssistant import *
from .StableBeluga2 import *
from typing import Tuple

def LoadLLM(model_name:str, system_message:str) -> Tuple[LLM, PromptGenerator]:
	if model_name.startswith("OpenAssistant"):
		return (
			OpenAssistantLLM(model_name),
			OpenAssistantPromptGenerator(system_message)
		)
	if model_name.startswith("stabilityai/StableBeluga2"):
		return (
			StableBeluga2()
		)