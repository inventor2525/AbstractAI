from AbstractAI.Model.Decorator import *
from AbstractAI.Helpers.log_caller_info import log_caller_info
from threading import Lock, get_ident
	
@DATA(generated_id_type=ID_Type.HASHID)
@dataclass
class CallerInfo:
	module_name: str
	function_name: str
	class_name: str
	instance_id: str
	file_path: str
	git_commit: str
	next: "CallerInfo" = None
	
	class Helper:
		lock = Lock()
		infos_by_thread = {}
		
		@staticmethod
		def pop() -> "CallerInfo":
			with CallerInfo.Helper.lock:
				thread_id = get_ident()
				if thread_id not in CallerInfo.Helper.infos_by_thread:
					return None
				return CallerInfo.Helper.infos_by_thread.pop(thread_id)[0]
			
		@staticmethod
		def catch_now(refer_to_next:bool, up_count:int) -> "CallerInfo":
			with CallerInfo.Helper.lock:
				thread_id = get_ident()
				
				caller_info: CallerInfo = None
				if thread_id not in CallerInfo.Helper.infos_by_thread:
					caller_info = CallerInfo(**log_caller_info(up_count))
					CallerInfo.Helper.infos_by_thread[thread_id] = (caller_info, refer_to_next)
				else:
					caller_info, prev_refer_to_next = CallerInfo.Helper.infos_by_thread[thread_id]
					if prev_refer_to_next:
						# We already have a caller info for this thread, so we need to
						# add a new one to the end of the stack.
						
						# Get the stack of caller infos.
						info_stack = [caller_info]
						next_caller_info = caller_info.next
						while next_caller_info:
							info_stack.append(next_caller_info)
							next_caller_info = next_caller_info.next
						
						# Add the new caller info to the end of the stack.
						info_stack[-1].next = CallerInfo(**log_caller_info(up_count))
						
						# Update the ids of the caller infos in the stack.
						for info in info_stack.__reversed__():
							info.new_id()
						
						# Update the refer_to_next boolean.
						CallerInfo.Helper.infos_by_thread[thread_id] = (caller_info, refer_to_next)
				return caller_info
				
	@staticmethod
	def get_caller_info(up_count:int=5, extra_up:int=0) -> "CallerInfo":
		CallerInfo.Helper.catch_now(refer_to_next=False, up_count=up_count+extra_up)
		return CallerInfo.Helper.pop()
	
	@staticmethod
	def catch_now(refer_to_next:bool, up_count:int=3, include_here=False, extra_up:int=0) -> "CallerInfo":
		"""
		Catches the caller info of the current thread now in a thread safe way
		so that it can be returned latter by get_caller_info.
		
		This makes it so that the caller info of a helper function can be saved
		as well.
		
		Args:
			refer_to_next: If true, this will hold a reference to the next caller info
				so that you can build a sparse stack trace.
		
		Returns:
			The caller info of the current execution point or if catch_now was called
			previously in the same thread after the last call to get_caller_info, then
			the caller info of the first call to catch_now. CallerInfo's will refer to
			the next caller info so long as refer_to_next is True. Once a call to catch
			now is made with refer_to_next=False, the next call to catch_now will
			return as before but no longer append to the stack trace, even if 
			a future call to catch_now is made with refer_to_next=True.
		"""
		if include_here and up_count>=3:
			caller_info = CallerInfo.Helper.catch_now(True, up_count=up_count+extra_up)
			CallerInfo.Helper.catch_now(refer_to_next, up_count=2+extra_up)
		else:
			caller_info = CallerInfo.Helper.catch_now(refer_to_next, up_count=up_count+extra_up)
		return caller_info
	
	@staticmethod
	def catch_here_and_caller(refer_to_next:bool=False) -> "CallerInfo":
		return CallerInfo.catch_now(refer_to_next=refer_to_next, include_here=True, extra_up=1)