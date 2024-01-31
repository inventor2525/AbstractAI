from AbstractAI.ConversationModel.ModelBase import *
from typing import Dict, Any

@ConversationDATA(generated_id_type=ID_Type.HASHID)
class ModelInfo:
	class_name: str
	model_name: str
	parameters: Dict[str, Any] = field(default_factory=dict)