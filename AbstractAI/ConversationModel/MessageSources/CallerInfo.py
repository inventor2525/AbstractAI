from AbstractAI.ConversationModel.ModelBase import *
from AbstractAI.Helpers.log_caller_info import log_caller_info
from threading import Lock, get_ident
	
@ConversationDATA(generated_id_type=ID_Type.HASHID)
class CallerInfo:
	module_name: str
	function_name: str
	class_name: str
	instance_id: str
	file_path: str
	git_commit: str
	
	class Helper:
		lock = Lock()
		infos_by_thread = {}
		
		@staticmethod
		def pop() -> "CallerInfo":
			with CallerInfo.Helper.lock:
				thread_id = get_ident()
				if thread_id not in CallerInfo.Helper.infos_by_thread:
					return None
				return CallerInfo.Helper.infos_by_thread.pop(thread_id)
			
		@staticmethod
		def catch_now() -> "CallerInfo":
			with CallerInfo.Helper.lock:
				thread_id = get_ident()
				
				caller_info: CallerInfo = None
				if thread_id not in CallerInfo.Helper.infos_by_thread:
					caller_info = CallerInfo(**log_caller_info(3))
					CallerInfo.Helper.infos_by_thread[thread_id] = caller_info
				else:
					caller_info = CallerInfo.Helper.infos_by_thread[thread_id]
				return caller_info
				
	@staticmethod
	def get_caller_info(up_count:int=5) -> "CallerInfo":
		caller_info = CallerInfo.Helper.pop()
		if caller_info:
			return caller_info
		return CallerInfo(**log_caller_info(up_count))
	
	@staticmethod
	def catch_now() -> "CallerInfo":
		return CallerInfo.Helper.catch_now()