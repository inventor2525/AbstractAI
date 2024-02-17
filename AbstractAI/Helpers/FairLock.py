import threading
from typing import Any, List
from collections import deque
from contextlib import contextmanager

class FairLock:
	def __init__(self):
		self.condition = threading.Condition()
		self.lock = threading.Lock()
		
		self.queue_lock = threading.Lock()
		self.queue = deque()
	
	def _ready_for(self, thread_id:Any) -> bool:
		with self.queue_lock:
			if len(self.queue)==0:
				self.queue.append(thread_id)
				return True
			if self.queue[0] == thread_id:
				return True
			if not thread_id in self.queue:
				self.queue.append(thread_id)
		return False
	
	def acquire(self):
		thread_id = threading.current_thread()
		with self.condition:
			while not self._ready_for(thread_id):
				self.condition.wait()
		self.lock.acquire()

	def release(self):
		self.lock.release()
		with self.queue_lock:
			self.queue.popleft()
		with self.condition:
			self.condition.notify_all()
	
	def __enter__(self):
		self.acquire()
		return self

	def __exit__(self, exc_type, exc_val, exc_tb):
		self.release()

if __name__ == "__main__":
	fair_lock = FairLock()
	
	class WorkerThread(threading.Thread):
		def __init__(self, fair_lock, thread_id):
			threading.Thread.__init__(self)
			self.fair_lock = fair_lock
			self.thread_id = thread_id

		def run(self):
			for _ in range(100):  # Run for a finite number of iterations
				with self.fair_lock:
					for i in range(100):
						print(f"Thread {self.thread_id} is running {i}th iteration")
	
	threads = []
	for i in range(0,10):
		threads.append(WorkerThread(fair_lock, i))
	
	for thread in threads:
		thread.start()
	print("All running")
	
	for thread in threads:
		thread.join()
	print("All done.")