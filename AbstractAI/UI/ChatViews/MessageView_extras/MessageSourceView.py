from AbstractAI.ConversationModel.MessageSources import *
from AbstractAI.UI.Support._CommonImports import *

def pascal_case(string:str) -> str:
	return " ".join([word.capitalize() for word in string.split(" ")])
	
class MessageSourceView(QWidget):
	@property
	def message_source(self) -> MessageSource:
		return self._message_source
	@message_source.setter
	def message_source(self, value:MessageSource):
		self._message_source = value
		if value is None:
			self.label.setText("Unknown\nSource:")
		else:
			self.label.setText(self._get_source_label(value))
		
	def __init__(self, message_source:MessageSource=None):
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
		
	def _get_source_label(self, message_source:MessageSource) -> str:
		if message_source is None:
			return "Unknown\nSource:"
		elif isinstance(message_source, UserSource):
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
				pascal_case(message_source.model_info.class_name),
				pascal_case(message_source.model_info.model_name),
			])
		elif isinstance(message_source, TerminalSource):
			return "Terminal:"
		elif isinstance(message_source, EditSource):
			most_original = EditSource.most_original(message_source)
			
			if most_original is None or most_original.source is None:
				return "Edited from\nUnknown Source:"
			else:
				other_description = self._get_source_label(most_original.source)
				other_description = other_description.replace(":", "")
				return "\n".join([
					"Edited from",
					f"{other_description} msg:"
				])
		else:
			return "Unknown\nSource:"