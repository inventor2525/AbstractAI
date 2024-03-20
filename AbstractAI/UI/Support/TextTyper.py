import sys
import time
from typing import Callable, List, Tuple
import pyautogui
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QClipboard
from threading import Lock
pyautogui.FAILSAFE = False

from AbstractAI.UI.Support.QtTaskQueue import QtTaskQueue

class TextTyper:
	def __init__(self, app):
		self.app = app
		self._queue = QtTaskQueue()
		self.current_clipboard_content = ""
		
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
			self.current_clipboard_content = clipboard.text()

			# Set the text to be typed to the clipboard
			clipboard.setText(text)
			
			# Trigger the paste operation
			pyautogui.hotkey('ctrl', 'v')
			
		self._queue.add_task(task)
		self._queue.add_task(lambda: self._restore_clipboard(), 1.0)
	
	def _restore_clipboard(self):
		clipboard = self.app.clipboard()
		clipboard.setText(self.current_clipboard_content)
		
	def un_type(self):
		"""
		Undoes the last typing action.
		"""
		def task():
			pyautogui.hotkey('ctrl', 'z')
		self._queue.add_task(task)
		
# Example usage
if __name__ == "__main__":
	app = QApplication(sys.argv)
	text_typer = TextTyper(app)
	text_to_type = "Sample transcribed text."
	
	time.sleep(2)  # Wait before starting typing
	text_typer.type_str(text_to_type)
	
	def run_typing_example():
		try:
			time.sleep(2)
			text_typer.type_str(text_to_type)
			time.sleep(1)
			text_typer.un_type()
			text_typer.un_type()
		except Exception as e:
			print(e)
	
	from threading import Thread
	Thread(target=run_typing_example).start()
	
	sys.exit(app.exec_())