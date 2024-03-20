from ._CommonImports import *

class ColoredFrame(QFrame):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.background_color = QColor(0, 0, 0)
		self.selected = False

	def paintEvent(self, event):
		if not self.selected:
			painter = QPainter(self)
			painter.fillRect(QRect(0, 0, self.width(), self.height()), self.background_color)
			
		super().paintEvent(event)

	def set_selected(self, selected):
		self.selected = selected
		self.update()