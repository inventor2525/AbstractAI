import datetime
import statistics
from typing import Dict, Any, List
from contextlib import contextmanager

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

	def get_stats(self) -> Dict[str, Any]:
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
	def __init__(self, should_log:bool=False, log_starts:bool=True, log_stops:bool=True, log_time_taken:bool=True, log_statistics:bool=True):
		self.timers:Dict[str, TimerStats] = {}
		self.should_log = should_log
		
		self.log_starts = log_starts
		self.log_stops = log_stops
		self.log_time_taken = log_time_taken
		self.log_statistics = log_statistics
		
		if Stopwatch.singleton is None:
			Stopwatch.singleton = self
		
		self.previous_keys:List[Any] = [None]
	
	def print(self, msg:str) -> str:
		print( "    " * (len(self.previous_keys)-1) + msg )
	
	def _bool(self, default:bool, passed:bool) -> bool:
		if passed is None:
			return default
		else:
			return passed
	
	def start(self, key:Any, details:str=None, should_log:bool=None):
		if key is None:
			return
		
		if self._bool(self.should_log and self.log_starts, should_log):
			if details is None:
				self.print(f"Starting {key}")
			else:
				self.print(f"Starting {key} {details}")
		if key not in self.timers:
			self.timers[key] = TimerStats()
		self.timers[key].start()

	def stop(self, key:Any, should_log:bool=None, log_time_taken:bool=None, log_statistics:bool=None) -> Dict[str, Any]:
		if key in self.timers:
			et = self.timers[key].stop()
			stats = self.timers[key].get_stats()
			if self._bool(self.should_log and self.log_stops, should_log):
				msg = f"Stopping {key}"
				if self._bool(self.log_time_taken, log_time_taken):
					msg += f" after: {et}"
				if self._bool(self.log_statistics, log_statistics):
					msg += f" && {stats}"
				self.print(msg)
			return stats
		else:
			return None
	
	def sequential(self, key:Any, details:str=None, should_log:bool=None, log_time_taken:bool=None, log_statistics:bool=None) -> Dict[str, Any]:
		stats = None
		if self.previous_keys[-1] is not None:
			stats = self.stop(self.previous_keys[-1], should_log, log_time_taken, log_statistics)
		self.start(key, details, should_log)
		self.previous_keys[-1] = key
		return stats
	
	def new_scope(self):
		self.previous_keys.append(None)
	
	def end_scope(self, should_log:bool=None, log_time_taken:bool=None, log_statistics:bool=None):
		if self.previous_keys[-1] is not None:
			self.stop(self.previous_keys[-1], should_log, log_time_taken, log_statistics)
		
		if len(self.previous_keys) > 1:
			self.previous_keys.pop()
	
	@contextmanager
	def timed_block(self, key:Any, details:str=None, log_start:bool=None, log_stop:bool=None, log_time_taken:bool=None, log_statistics:bool=None):
		self.start(key, details, log_start)
		yield
		self.stop(key, log_stop, log_time_taken, log_statistics)