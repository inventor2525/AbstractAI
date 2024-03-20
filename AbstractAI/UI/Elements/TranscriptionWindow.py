from PyQt5.QtWidgets import QTextEdit, QWidget, QVBoxLayout
from PyQt5.QtCore import Qt, QRect
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QDesktopWidget
from PyQt5.QtGui import QCursor

class TranscriptionWindow(QWidget):
	def __init__(self):
		super().__init__()

		# Setting up the window
		self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
		self.setAttribute(Qt.WA_TranslucentBackground)

		# Setting up the layout and text edit
		layout = QVBoxLayout()
		self.text_edit = QTextEdit()
		self.text_edit.setReadOnly(True)

		# Customize text edit for two different fonts/colors
		self.fixed_transcription_font = QFont("Arial", 12)
		self.live_transcription_font = QFont("Arial", 12)

		layout.addWidget(self.text_edit)
		self.setLayout(layout)

		# Set an initial size
		self.setGeometry(100, 100, 400, 200)

	def update_transcription(self, fixed_transcription, live_transcription):
		# Check if the scroll bar is at the bottom before updating
		scroll_bar = self.text_edit.verticalScrollBar()
		at_bottom = scroll_bar.value() == scroll_bar.maximum()

		self.text_edit.clear()
		self.text_edit.setCurrentFont(self.fixed_transcription_font)
		self.text_edit.setTextColor(Qt.black)
		self.text_edit.insertPlainText(fixed_transcription)

		self.text_edit.setCurrentFont(self.live_transcription_font)
		self.text_edit.setTextColor(Qt.darkGray)
		self.text_edit.insertPlainText(live_transcription)

		# If the scroll bar was at the bottom, move it back to the bottom
		if at_bottom:
			scroll_bar.setValue(scroll_bar.maximum())

	def showNearCursor(self):
		cursor_pos = QCursor.pos()
		screen_rect = QDesktopWidget().availableGeometry(cursor_pos)
		window_rect = self.geometry()

		# Adjust window position to ensure it fits on the screen
		x = min(cursor_pos.x(), screen_rect.right() - window_rect.width())
		y = min(cursor_pos.y(), screen_rect.bottom() - window_rect.height())
		self.move(x, y)
		self.show()
		
if __name__ == '__main__':
	import sys
	from PyQt5.QtWidgets import QApplication

	# Assuming the TranscriptionWindow class is defined as previously discussed

	app = QApplication(sys.argv)

	# Create an instance of the TranscriptionWindow
	transcription_window = TranscriptionWindow()

	# Update the transcription texts for demonstration
	fixed_transcription = "Fixed transcription text in one font. UserI have a PyQt app for transcribing audio. It displays a red-green indicator at the top left. I want you to make a window similar to it where there's no border or anything else. I want it to be a simple text box that uses CSS styling to display a string that will be live updated by the transcription thing later. I just want the Qt view to be something that I can call a show method, call a hide method, or a close method rather. The text box should display two strings, one in one color and one in the other color, following each other as one long string. The thing is, this transcription thing is going to return a fixed transcription that's been run through a larger model and then a live transcription that's running through a smaller model locally. That smaller model is going to make a lot of mistakes, so I want it to display in a different font. So, one text box, two fonts, the two strings will be appended to each other in different fonts. And I want a property for both the fixed and the live transcription that lets me change either one. I'm updating in each case the Qt view.    when the open / show method is called, it should show at the cursor, but fit on the screen, so don't just put it's top left corner at the cursor, figure out where the cursor is, and then what rect would fit on the screen.... also, resize the view to fit the text, and turn it into a scroll view once it reaches a certain size "
	live_transcription = "Live transcription text in a different font."
	transcription_window.update_transcription(fixed_transcription, live_transcription)

	# Show the window near the cursor
	transcription_window.showNearCursor()
	#transcription_window.hide()
	sys.exit(app.exec_())