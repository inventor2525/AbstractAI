from AbstractAI.Model.Decorator import *
from typing import Dict, Any


#This is a legacy class that is no longer used, here only 
#to support legacy database entries and can be removed 
#completely and safely for new users.

#Do not extend use or access instances of it unless you have
#legacy data like I do.

#Model config is now stored in LLMSettings and is loaded directly
#into the database. This class was here to point to it in json
#rather than acting as a single point of truth for the model like
#it should have been.


@DATA(generated_id_type=ID_Type.HASHID)
@dataclass
class ModelInfo:
	'''
	This is legacy code that supports the
	'''
	class_name: str
	model_name: str
	parameters: Dict[str, Any] = field(default_factory=dict)
	config: Dict[str, Any] = field(default_factory=dict, init=False)