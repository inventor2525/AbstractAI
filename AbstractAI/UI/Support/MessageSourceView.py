from AbstractAI.Conversation.MessageSources import *
from ._CommonImports import *

def pascal_case(string:str) -> str:
	return " ".join([word.capitalize() for word in string.split(" ")])
	
class MessageSourceView(QWidget):
	def __init__(self, message_source:BaseMessageSource):
		super().__init__()
		self.message_source = message_source
		
		self.layout = QVBoxLayout()
		self.layout.setContentsMargins(0, 0, 0, 0)
		
		self.setLayout(self.layout)
		
		if message_source is None:
			self.layout.addWidget(QLabel("Unknown\nSource:"))
		elif isinstance(message_source, UserSource):
			self.layout.addWidget(QLabel(f"{pascal_case(message_source.user_name)}:"))
		elif isinstance(message_source, ModelSource):
			self.layout.addWidget(QLabel("Model:"))
			self.layout.addWidget(QLabel(f"{pascal_case(message_source.class_name)}"))
			self.layout.addWidget(QLabel(f"{pascal_case(message_source.model_name)}"))
		elif isinstance(message_source, TerminalSource):
			self.layout.addWidget(QLabel("Terminal:"))
		elif isinstance(message_source, EditSource):
			most_original = EditSource.most_original(message_source)
			self.layout.addWidget(QLabel("Edited from:"))
			if most_original is None or most_original.source is None:
				self.layout.addWidget(QLabel("Unknown Source"))
			else:
				self.layout.addWidget(QLabel(type(most_original.source).__name__))
		else:
			self.layout.addWidget(QLabel("Unknown Source"))
	