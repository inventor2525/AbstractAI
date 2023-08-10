import datetime
import statistics

class TimerStats:
	def __init__(self):
		self.times = []
		self.start_time = None

	def start(self):
		self.start_time = datetime.datetime.now()

	def stop(self):
		if self.start_time is not None:
			elapsed_time = datetime.datetime.now() - self.start_time
			self.times.append(elapsed_time.total_seconds())
			self.start_time = None
			return elapsed_time

	def get_stats(self):
		if len(self.times) > 0:
			return {
				'last': self.times[-1],
				'average': statistics.mean(self.times),
				'min': min(self.times),
				'max': max(self.times),
				'std_dev': statistics.stdev(self.times) if len(self.times) > 1 else 0
			}
		else:
			return None

class Stopwatch:
	singleton = None
	def __init__(self, debug=True):
		self.timers = {}
		self.debug = debug
		if Stopwatch.singleton is None:
			Stopwatch.singleton = self
		
	def start(self, key, details:str=None):
		if self.debug:
			if details is None:
				print("Starting ", key)
			else:
				print(f"Starting {key} {details}")
		if key not in self.timers:
			self.timers[key] = TimerStats()
		self.timers[key].start()

	def stop(self, key):
		if key in self.timers:
			et = self.timers[key].stop()
			stuff = self.timers[key].get_stats()
			if self.debug:
				print(f"Stopping {key} which ran for {et} && {stuff}")
			return stuff
		else:
			return None
