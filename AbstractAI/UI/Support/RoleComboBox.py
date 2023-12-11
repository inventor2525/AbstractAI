from AbstractAI.ConversationModel import *
from ._CommonImports import *

class RoleComboBox(QComboBox):
	def __init__(self, values:List[str], default_value:str="Human", *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.setEditable(True)
		self.default_value = default_value
		self.addItems(values)
		self.set_default_value()
		#do not auto complete
		self.completer().setCompletionMode(QCompleter.UnfilteredPopupCompletion)
		self.setInsertPolicy(QComboBox.NoInsert)
		
	def set_default_value(self):
		index = self.findText(self.default_value)
		if index != -1:
			self.setCurrentIndex(index)
