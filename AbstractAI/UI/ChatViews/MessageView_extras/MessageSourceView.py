from ClassyFlaskDB.DefaultModel import Object
from AbstractAI.Model.Converse.MessageSources import *
from AbstractAI.UI.Support._CommonImports import *

def pascal_case(string:str) -> str:
	return " ".join([word.capitalize() for word in string.split(" ")])
	
class MessageSourceView(QWidget):
	@property
	def message_source(self) -> Object:
		return self._message_source
	@message_source.setter
	def message_source(self, value:Object):
		self._message_source = value
		self.label.setText(self._get_source_label(value))
		
	def __init__(self, message_source:Object=None):
		super().__init__()
		
		self.init_ui()
		self.message_source = message_source
	
	def init_ui(self):
		# Create a layout
		self.setFixedWidth(75)
		self.layout = QVBoxLayout()
		self.layout.setContentsMargins(0, 0, 0, 0)
		self.setLayout(self.layout)
		
		# Create a label to display the source of the message
		self.label = QLabel()
		self.layout.addWidget(self.label)
		
	def _get_source_label(self, message_source:Object) -> str:
		try:
			if isinstance(message_source, UserSource):
				if message_source.user_name is None or message_source.user_name == "":
					return "Message from\nUnknown User:"
				elif message_source.user_name.lower() == "system":
					return "System:"
				else:
					return "\n".join([
						"Msg from",
						f"{pascal_case(message_source.user_name)}:"
					])
			elif isinstance(message_source, ModelSource):
					return "\n".join([
						"Model",
						message_source.settings.__ui_name__,
						message_source.settings.user_model_name,
					])
			elif isinstance(message_source, FilesSource):
				return "Files"
			elif isinstance(message_source, EditSource):
				most_original = message_source.original_object()
				
				if most_original is None or most_original.source is None:
					return "Edited from\nUnknown Source:"
				else:
					other_description = self._get_source_label(most_original.source)
					other_description = other_description.replace(":", "")
					return "\n".join([
						"Edited from",
						f"{other_description} msg:"
					])
		except Exception as e:
			pass
		return "Unknown\nSource:"