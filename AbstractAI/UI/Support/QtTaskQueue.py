from typing import Callable, List, Tuple
from PyQt5.QtCore import QTimer
from threading import Lock

class QtTaskQueue:
	def __init__(self, min_run_interval=100):
		self.task_queue: List[Tuple[float, Callable[[], None]]] = []
		self.lock = Lock()
		
		self.task_running = False
		
		self.timer = QTimer()
		self.timer.timeout.connect(self._process_tasks)
		self.timer.start(min_run_interval)
	
	def add_task(self, task: Callable[[], None], delay: float = 0):
		with self.lock:
			self.task_queue.append((delay, task))
		self._attempt_process_now()
		
	def clear(self, debug=False):
		with self.lock:
			if debug:
				print(f"Clearing {len(self.task_queue)} tasks")
			self.task_queue.clear()
			self.task_running = False
			
	def _attempt_process_now(self):
		try:
			QTimer.singleShot(0, self._process_tasks)
		except Exception as e:
			pass
	
	def _process_tasks(self):
		def execute_task(task: Callable[[], None]):
			with self.lock:
				if not self.task_running:
					return
			task()
			with self.lock:
				self.task_running = False
			
		with self.lock:
			if self.task_running or not self.task_queue:
				return
			
			self.task_running = True
			delay, task = self.task_queue.pop(0)
			
		if delay <= 0:
			execute_task(task)
		else:
			QTimer.singleShot(int(delay * 1000), lambda: execute_task(task))

# Usage Example
if __name__ == '__main__':
	from PyQt5.QtWidgets import QApplication
	import sys
	
	app = QApplication(sys.argv)
	
	task_queue = QtTaskQueue()
	
	def task():
		print("Hello World!")
	
	task_queue.add_task(task)
	task_queue.add_task(task, 1)
	task_queue.add_task(task, 2)
	
	
	from threading import Thread
	import time
	Thread(target=task_queue.add_task, args=(task, 1)).start()
	Thread(target=task_queue.add_task, args=(task, 1)).start()
	def clear():
		time.sleep(2)
		task_queue.clear(debug=True)
		print("Cleared!")
	Thread(target=clear).start()
	sys.exit(app.exec_())
		