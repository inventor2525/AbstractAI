from AbstractAI.UI.Support._CommonImports import *
import math
import time

class FlashingButton(QPushButton):
	def __init__(self, *args, interval:float, min_color:QColor, max_color:QColor, **kwargs):
		'''
		FlashingButton is a QPushButton that flashes between min_color and max_color
		:param interval: The interval in seconds between flashes
		:param min_color: The minimum color
		:param max_color: The maximum color
		:param args: QPushButton args
		:param kwargs: QPushButton kwargs
		'''
		super().__init__(*args, **kwargs)
		
		self.interval = interval
		self.min_color = min_color
		self.max_color = max_color
		self._flashing = False
		self._timer = None
		
	def strobe(self):
		def clamp(val):
			return max(0, min(255, val))
		val = math.sin(time.time() * (1/self.interval))
		r = clamp(self.min_color.red() + (self.max_color.red() - self.min_color.red()) * val)
		g = clamp(self.min_color.green() + (self.max_color.green() - self.min_color.green()) * val)
		b = clamp(self.min_color.blue() + (self.max_color.blue() - self.min_color.blue()) * val)
		self.setStyleSheet(f"background-color: rgba({r}, {g}, {b}, 255);")
	
	@property
	def flashing(self):
		return self._flashing
	@flashing.setter
	def flashing(self, value:bool):
		if value and not self._flashing:
			self._timer = QTimer()
			self._timer.timeout.connect(self.strobe)
			self._timer.start(50)
		self._flashing = value
		if not value:
			self._timer.stop()
			self._timer = None