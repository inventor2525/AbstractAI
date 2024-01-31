from AbstractAI.ConversationModel.MessageSources import *
from ._CommonImports import *

def pascal_case(string:str) -> str:
	return " ".join([word.capitalize() for word in string.split(" ")])
	
class MessageSourceView(QWidget):
	def __init__(self, message_source:MessageSource):
		super().__init__()
		
		self.layout = QVBoxLayout()
		self.layout.setContentsMargins(0, 0, 0, 0)
		
		self.setLayout(self.layout)
		self.label = QLabel()
		self.layout.addWidget(self.label)
		
		self.set_message_source(message_source)
	
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
		
	def set_message_source(self, message_source:MessageSource):
		self.message_source = message_source
		self.label.setText(self._get_source_label(message_source))
	