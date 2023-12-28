import inspect
import subprocess
from typing import Dict, Optional
import os

# Dictionary for caching commit hashes
commit_cache = {}

def get_git_commit(directory: str) -> str:
	"""
	Find the Git commit hash for a given directory.

	This function traverses upwards from the given directory to find the root of the Git repository,
	then retrieves the current commit hash.

	Args:
	directory (str): The directory from which to start searching for a Git repository.

	Returns:
	str: The current Git commit hash if found, otherwise a descriptive error message.
	"""

	def find_git_directory(dir_path: str) -> Optional[str]:
		"""
		Traverse upwards from the given directory to find the .git directory.
		"""
		current_dir = dir_path
		while current_dir != os.path.dirname(current_dir):  # Check until the root directory
			if os.path.isdir(os.path.join(current_dir, ".git")):
				return current_dir
			current_dir = os.path.dirname(current_dir)
		return None

	# Find the Git repository root directory
	git_root = find_git_directory(directory)
	if git_root is None:
		return "Not a Git repository"

	try:
		git_dir = os.path.join(git_root, ".git")
		commit_hash = subprocess.check_output(
			['git', '--git-dir', git_dir, '--work-tree', git_root, 'rev-parse', 'HEAD']
		).strip().decode('utf-8')
		return commit_hash
	except subprocess.CalledProcessError as e:
		return str(e)

def log_caller_info(up_count:int=0) -> Dict[str, str]:
	"""
	Gather information about the caller of this function, including module, class, and method details.

	This function inspects the call stack to find the caller's module name, file path, class name & id (if
	applicable), and the function/method name. It also retrieves the current Git commit hash of the caller's module.

	Args:
	up_count (int): How many frames to go up in the call stack before retrieving the caller's information.
					Defaults to 0, which is the immediate caller of this function.
					This is useful if you want to log information about the caller of the caller, etc.

	Returns:
	Dict[str, str]: A dictionary containing the 'module_name', 'function_name', 'class_name', 'file_path',
					and the 'git_commit' hash of the calling context.
	"""
	frame = inspect.currentframe()
	caller_frame = frame.f_back
	
	while up_count > 0 and caller_frame is not None:
		caller_frame = caller_frame.f_back
		up_count -= 1
		
	module = inspect.getmodule(caller_frame)
	module_name = module.__name__ if module else "Unknown"
	file_path = caller_frame.f_code.co_filename

	class_name = ""
	instance_id = ""
	function_name = caller_frame.f_code.co_name

	while caller_frame:
		local_self = caller_frame.f_locals.get('self')
		if local_self:
			class_name = local_self.__class__.__qualname__
			instance_id = hex(id(local_self))
			break
		caller_frame = caller_frame.f_back
		if caller_frame is not None and caller_frame.f_code.co_name != '<module>':
			function_name = f"{caller_frame.f_code.co_name}.{function_name}"

	# Get the directory of the calling module
	module_directory = os.path.dirname(file_path)

	return {
		'module_name': module_name,
		'function_name': function_name,
		'class_name': class_name,
		'instance_id': instance_id,
		'file_path': file_path,
		'git_commit': get_git_commit(module_directory)
	}
