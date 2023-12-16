from AbstractAI.ConversationModel.MessageSources import *
from AbstractAI.UI.Support._CommonImports import *

class RollingColorPallet:
	def __init__(self):
		self._colors = QColor.colorNames()#  ['red', 'green', 'blue', 'yellow', 'cyan', 'magenta', 'gray']
		self._index = 0
	
	def next_color(self) -> str:
		color = self.colors[self._index % len(self._colors)]
		self._index += 1
		return color

class RoleColorPallet:
	def __init__(self):
		self._colors = {
			UserSource:{
				"system": "lightgrey",
				"user": "#9DFFA6",
			},
			ModelSource:"#FFC4B0",
			TerminalSource:"#FFEBE4",
			EditSource:"#9DFFA6",
		}
		self._rolling_pallet = RollingColorPallet()
	
	def get_color(self, source:MessageSource) -> QColor:
		if source is None:
			return QColor(Qt.white)
		
		#TODO: Get the non EditSource message source from source
		
		inner = self._colors.get(type(source), "#FFFFFF")
		if isinstance(inner, dict):
			# source is a user source (so far)
			lower_name = source.user_name.lower()
			if lower_name in inner:
				return QColor(inner[lower_name])
			
			if source.user_name not in inner:
				inner[source.user_name] = self._rolling_pallet.next_color()
			return QColor(inner[source.user_name])
		return QColor(inner)