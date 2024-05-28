from ClassyFlaskDB.DefaultModel import *
from AbstractAI.Helpers.log_caller_info import log_caller_info
from threading import Lock, get_ident
from typing import Optional


@DATA(generated_id_type=ID_Type.HASHID, hashed_fields=["module_name", "function_name", "class_name", "instance_id", "file_path", "git_commit"])
@dataclass
class CallerInfo(Object):
	module_name: str = None
	function_name: str = None
	class_name: str = None
	instance_id: str = None
	file_path: str = None
	git_commit: str = None
	
	@staticmethod
	def catch(points:List[int]=[0], excluded_fields:List[str]=[], key:Optional[str]=None) -> "CallerInfo":
		'''
		Gets a sparse stack trace of who called this function.
		
		Args:
			points:a list of numbers [0,stack size] where each number
			represents how many callers up from who called catch we're
			going to save. So if you want to catch who is calling catch
			just leave the default [0] but if you want that, who is calling
			it, and who is calling that, you can do [0,1,2]. Numbers do
			not need to be consecutive!
			
			excluded_fields:Some fields are slow to get, if you don't want
			all you can exclude some and they will be left None
			
			key:if passed you can save from getting info for the same
			caller repeatedly by storing it in a static dictionary.
		
		Returns:
			A caller info where it's source may be the next level up in a
			sparse stack trace.
		'''
		if key is not None and key in CallerInfo.catches:
			return CallerInfo.catches[key]
		
		if points is None or len(points)==0:
			points = [0]
		elif len(points)>1:
			points = sorted(set(points), reverse=True)
		
		source = None
		for point in points:
			source = CallerInfo(source=source, **log_caller_info(point+1, excluded_fields))
		
		if key is not None:
			CallerInfo.catches[key] = source
		return source
CallerInfo.catches = {}

if __name__ == "__main__":
	engine = DATAEngine(DATA)
	import json
	class TestClass1:
		def thing1(self):
			class test_class2:
				def test2(self):
					ci = CallerInfo.catch([0,1])
					print(ci)
			test_class2().test2()
						
	TestClass1().thing1()