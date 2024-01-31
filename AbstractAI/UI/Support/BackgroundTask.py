from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

from typing import Callable, List, Tuple, Any
class BackgroundTask(QThread):
	busy_indication = pyqtSignal()

	def __init__(self, task: Callable[[], Any], background_interval: int = 10):
		super().__init__()
		self.task = task
		self.timmer = QTimer()
		self.timmer.setInterval(background_interval)
		self.timmer.timeout.connect(self.busy_indication.emit)

	def run(self):
		self.return_val = self.task()

	def start(self):
		self.timmer.start()
		self.finished.connect(self.timmer.stop)
		super().start()
