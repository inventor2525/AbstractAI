from PyQt5.QtCore import QObject, pyqtSignal, QThread
from functools import wraps

# This QObject derivative will hold the signal and ensure it's connected to the main thread
class SignalEmitter(QObject):
    # Define a signal capable of carrying any callable and its arguments
    trigger = pyqtSignal(object, tuple, dict)

    def __init__(self):
        super().__init__()
        # Ensure this object lives in the main thread
        self.moveToThread(QThread.currentThread())
        self.trigger.connect(self.slot)

    def slot(self, func, args, kwargs):
        # Execute the function with provided arguments
        func(*args, **kwargs)

# Singleton pattern to ensure one emitter is used application-wide
emitter_instance = SignalEmitter()

def run_in_main_thread(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Emit the signal with the function and arguments
        emitter_instance.trigger.emit(func, args, kwargs)
    return wrapper

if __name__ == "__main__":
	# Usage example
	@run_in_main_thread
	def target_function():
		# This function will run in the main thread
		print("This is running in the main thread.")

	# Assuming `target_function` is called from a different thread,
	# it will actually execute in the main thread.
