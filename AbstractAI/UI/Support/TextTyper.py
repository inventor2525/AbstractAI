import sys
import time
import pyautogui
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QClipboard

pyautogui.FAILSAFE = False

class TextTyper:
	def __init__(self, app: QApplication):
		self.app = app
		self.task_queue = []
		self.timer = QTimer()
		self.timer.timeout.connect(self.process_tasks)
		self.timer.start(100)  # Adjust the interval as needed

	def add_task(self, task):
		self.task_queue.append(task)

	def process_tasks(self):
		while self.task_queue:
			task = self.task_queue.pop(0)
			task()

	def type_str(self, text: str):
		def task():
			########################################
			# Method 1: Copy to clipboard and paste
			########################################
			# current_clipboard_content = pyperclip.paste()
			# pyperclip.copy(text)
			# time.sleep(0.01)  # Sleep for 10ms to ensure clipboard is updated
			# pyautogui.hotkey('ctrl', 'v')
			# time.sleep(0.01)
			# pyperclip.copy(current_clipboard_content)

			########################################
			# Method 2: Direct typing
			########################################
			# pyautogui.typewrite(text, interval=0.0001)

			########################################
			# Method 3: Writing the text
			########################################
			# pyautogui.write(text)
			
			########################################
			# Method 4: Using QClipboard
			########################################
			# Get the current clipboard content
			clipboard = self.app.clipboard()
			current_clipboard_content = clipboard.text()

			# Set the text to be typed to the clipboard
			clipboard.setText(text)
			
			# Trigger the paste operation
			pyautogui.hotkey('ctrl', 'v')
			
			# Set a timer to restore the original clipboard content
			def _restore_clipboard(self, content):
				clipboard = self.app.clipboard()
				clipboard.setText(content)
			QTimer.singleShot(1000, lambda: _restore_clipboard(self, current_clipboard_content))
		self.add_task(task)

	def un_type(self):
		"""
		Undoes the last typing action.
		"""
		def task():
			pyautogui.hotkey('ctrl', 'z')
		self.add_task(task)
		
# Example usage
if __name__ == "__main__":
	app = QApplication(sys.argv)
	text_typer = TextTyper(app)
	text_to_type = "Sample transcribed text."
	
	
	# time.sleep(2)  # Wait before starting typing
	# text_typer.type_str(text_to_type)
	
	def run_typing_example():
		try:
			time.sleep(2)
			text_typer.type_str(text_to_type)
			time.sleep(1)
			text_typer.un_type()
		except Exception as e:
			print(e)
	
	#QThread
	from PyQt5.QtCore import QThread
	class TypingThread(QThread):
		def run(self):
			run_typing_example()
	
	#start:
	typing_thread = TypingThread()
	typing_thread.start()
	
	sys.exit(app.exec_())