from time import sleep
from typing import Callable, TypeVar, Generic, List, Set, Optional, Dict, Any, Tuple, Type
from typing_extensions import ParamSpec
from threading import Lock, Thread, Condition
from AbstractAI.Helpers.FairLock import FairLock
from dataclasses import field
import traceback
# Define a ParamSpec for the arguments and a TypeVar for the return type
P = ParamSpec('P')
R = TypeVar('R')

class Signal(Generic[P, R]):
	def __init__(self):
		self._listeners: Dict[Optional[str], Tuple[Callable[P, R], bool]] = {}
		self.lock = Lock()
		self.lockie = ""

	def connect(self, listener: Callable[P, R], key: Optional[str] = None, auto_disconnect:bool=False) -> None:
		print("connect locking")
		with self.lock:
			self.lockie = "connect"
			if key is None:
				key = listener
			self._listeners[key] = (listener, auto_disconnect)
			print("connect unlocked")
			self.lockie = ""

	def disconnect(self, listener: Callable[P, R], key: Optional[str] = None) -> None:
		print("disconnect locking")
		with self.lock:
			self.lockie = "disconnect"
			try:
				print("Disconnect locked")
				if key is None:
					key = listener
				
				print("Disconnect key none done")
				if key in self._listeners:
					del self._listeners[key]
				print("del done")
			except Exception as e:
				print("WTF disconnect")
			print("disconnect unlocked")
			self.lockie = ""

	def _call(self, listeners: Dict[Optional[str], Tuple[Callable[P, R], bool]], *args: P.args, **kwargs: P.kwargs) -> Dict[str, R]:
		results: Dict[str, R] = {}
		print("_call running...")
		for key, listener in listeners.items():
			try:
				print(f"calling {listener[0]} with {args} and {kwargs}")
				r = listener[0](*args, **kwargs)
				print("listener called successfully")
				if isinstance(key, str):
					results[key] = r
			except Exception as e:
				print("error calling listener")
				print(f"e={e}")
				print("Stack trace:")
				traceback.print_exc()
				if listener[1]:
					print("listener[1]")
					self.disconnect(listener[0], key)
					print("disconnected")
				else:
					print("e")
					raise e
				
		return results
	
	def __call__(self, *args: P.args, **kwargs: P.kwargs) -> Dict[str, R]:
		print("__call__ locking")
		with self.lock:
			self.lockie = "__call__"
			listeners = dict(self._listeners)
			print("__call__ unlocking")
			self.lockie = ""
		return self._call(listeners, *args, **kwargs)
	
	def __deepcopy__(self, memo):
		return self
	
	@classmethod
	def field(cls, compare=False, repr=False, hash=False, init=False, kw_only=True) -> field:
		return field(default_factory=cls, compare=compare, repr=repr, hash=hash, init=init, kw_only=kw_only)

class LazySignal(Signal[P, R]):
	def __init__(self, timeout: float = 0.2):
		super().__init__()
		self.lock = FairLock()
		self.dirty = False
		self.timeout = timeout
		self.condition = Condition()
		
		self.thread_running = False
			
	def _run(self):
		while True:
			with self.condition:
				if not self.dirty:
					self.condition.wait(1)
			
			print("_run locking")
			with self.lock:
				print("_run locked")
				self.lockie = "_run"
				if not self.dirty:
					self.thread_running = False
					return
				print("if not self.dirty done")
				self.dirty = False
				listeners = self._listeners.copy()
				print("self._listeners.copy() done")
				print(f"running:{listeners}")
				self._call(listeners, *self.args, **self.kwargs)
				print("_run un-locking")
				
				self.lockie = ""
			sleep(self.timeout)

	def __call__(self, *args: P.args, **kwargs: P.kwargs):
		print("hello call")
		print(f"Locked on '{self.lockie}'")
		with self.lock:
			self.lockie = "__call__"
			print("call lock")
			self.args = args
			self.kwargs = kwargs
			self.dirty = True
			
			if not self.thread_running:
				self.thread_running = True
				
				print("creating thread")
				self.thread = Thread(target=self._run)
				self.thread.daemon = True
				self.thread.start()
				print("thread started")
			self.lockie = ""
		print("unlock")
		with self.condition:
			print("notifying...")
			self.condition.notify_all()
		print("lazy signal call done")
			
if __name__ == "__main__":
	# Example usage with different listener signatures
	def listener1(x: int, y: str) -> float:
		return len(y) * x
	
	def listener1_2(x: int, y: str) -> float:
		return len(y) * x * 5

	def listener2(x: int) -> int:
		return x * 2

	def listener3() -> str:
		return "No arguments"

	# Create signal instances with different signatures
	signal1 = Signal[[int, str], float]()
	signal2 = Signal[[int], int]()
	signal3 = Signal[[], str]()

	# Connect listeners
	signal1.connect(listener1, "bla")
	signal1.connect(listener1, "listener1")
	signal1.connect(listener1_2, "listener1_2")
	
	signal2.connect(listener2, "listener2")
	signal3.connect(listener3, "listener3")

	# Call the signals
	result1 = signal1(5, "hello")
	result2 = signal2(10)
	result3 = signal3()

	print("Result 1:", signal1(5, "hello"))
	signal1.disconnect("bla")
	
	print("Result 1 (post remove):", signal1(5, "hello"))
	signal1.connect(listener1)
	
	print("Result 1 (post re-add):", signal1(5, "hello"))
	
	print("Result 2:", signal2(10))
	print("Result 3:", signal3())
