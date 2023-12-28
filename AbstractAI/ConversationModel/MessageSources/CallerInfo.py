from AbstractAI.ConversationModel.ModelBase import *
from AbstractAI.Helpers.log_caller_info import log_caller_info

@ConversationDATA(generated_id_type=ID_Type.HASHID)
class CallerInfo:
	module_name: str
	function_name: str
	class_name: str
	instance_id: str
	file_path: str
	git_commit: str
	
	@staticmethod
	def get_caller_info():
		caller_info = log_caller_info(5)
		return CallerInfo(**caller_info)