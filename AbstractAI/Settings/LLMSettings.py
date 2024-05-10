from AbstractAI.ConversationModel import ConversationDATA
from AbstractAI.LLMs.CommonRoles import CommonRoles
from dataclasses import field
from typing import List
from typing import Dict

@ConversationDATA
class RolesSettings:
	must_alternate:bool = False
	merge_consecutive_messages_by_same_role:bool = False
	mapping:Dict[CommonRoles, str] = field(default_factory=lambda: {
		CommonRoles.System: "system",
		CommonRoles.User: "user",
		CommonRoles.Assistant: "assistant"
	})

@ConversationDATA
class LLMSettings:
	user_model_name:str = ""
	user_description:str = ""
	roles:RolesSettings = RolesSettings()
	
	def load(self) -> "LLM":
		raise NotImplementedError("Subclasses must implement this method.")

@ConversationDATA
class LLMConfigs:
	models:List[LLMSettings] = field(default_factory=list)