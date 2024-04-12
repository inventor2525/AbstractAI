from .UserSource import *
from typing import List, Iterable, Tuple
import os
import re

@ConversationDATA(generated_id_type=ID_Type.HASHID, hashed_fields=["path"])
class ItemModel:
	def __init__(self, path):
		self.path = path
	
	@staticmethod
	def iterate_files(items:List['ItemModel']) -> Iterable[str]:
		def explore_folder(folder_path, file_pattern='', folder_pattern='', allowed_extensions=set()):
			try:
				for entry in os.listdir(folder_path):
					full_path = os.path.join(folder_path, entry)
					if os.path.isdir(full_path):
						if not folder_pattern or re.match(folder_pattern, entry):
							yield from explore_folder(full_path, file_pattern, folder_pattern, allowed_extensions)
					elif os.path.isfile(full_path):
						if not file_pattern or re.match(file_pattern, entry):
							extension = os.path.splitext(full_path)[1][1:]
							if allowed_extensions and extension not in allowed_extensions:
								continue
							yield full_path
			except PermissionError:
				pass

		for item in items:
			if isinstance(item, FolderModel):
				yield from explore_folder(item.path, item.file_pattern, item.folder_pattern, item.allowed_extensions)
			else:
				yield item.path

@ConversationDATA(generated_id_type=ID_Type.HASHID, hashed_fields=["path", "file_pattern", "folder_pattern", "extension_pattern"])
class FolderModel(ItemModel):
	def __init__(self, path, file_pattern='', folder_pattern='', extension_pattern=''):
		super().__init__(path)
		self.file_pattern = file_pattern
		self.folder_pattern = folder_pattern
		self.extension_pattern = extension_pattern

	@property
	def allowed_extensions(self):
		if self.extension_pattern:
			return set(self.extension_pattern.replace(',', ' ').split())
		return set()

@ConversationDATA(generated_id_type=ID_Type.HASHID, hashed_fields=["items"])
class ItemsModel:
	items:List[ItemModel] = field(default_factory=list, kw_only=True)
	
	def new_id(self):
		for item in self.items:
			item.new_id()

@ConversationDATA
class FilesSource(UserSource):
	'''Describes the source of a message from a person.'''
	items:ItemsModel = field(default_factory=ItemsModel, kw_only=True)
	loaded:datetime = field(default_factory=get_local_time, kw_only=True)
	
	def load(self) -> str:
		new_content = []
		extension_md_map = {
			"py": "python",
			"js": "javascript",
			"html": "html",
			"cpp": "cpp",
			"c": "c",
			"h": "c",
			"java": "java",
			"json": "json",
			"xml": "xml",
			"yaml": "yaml",
			"yml": "yaml",
			"txt": "text",
			"md": "markdown",
			"css": "css",
			"sh": "bash",
			"bat": "batch",
		}
		for path in ItemModel.iterate_files(self.items):
			new_content.append(path)
			extension = os.path.splitext(path)[1][1:]
			markdown = extension_md_map.get(extension, 'text')
			new_content.append(f"```{markdown}")
			with open(path, 'r') as file:
				new_content.append(file.read())
			new_content.append("```\n")
		new_source = FilesSource(items=self.items)
		self.loaded = get_local_time()
		return '\n'.join(new_content)