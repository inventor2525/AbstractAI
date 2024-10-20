from PyQt5.QtWidgets import QWidget, QHBoxLayout, QPushButton, QScrollArea, QSizePolicy
from PyQt5.QtCore import Qt, QSize
from AbstractAI.AppContext import AppContext
from AbstractAI.Model.Converse import Conversation
from AbstractAI.Helpers.run_in_main_thread import run_in_main_thread

class ConversationTab(QWidget):
	def __init__(self, conversation: Conversation, height: int):
		super().__init__()
		self.conversation = conversation
		self.height = height
		self.init_ui()

	def init_ui(self):
		layout = QHBoxLayout(self)
		layout.setContentsMargins(0, 0, 0, 0)
		layout.setSpacing(0)

		self.select_button = QPushButton(self.conversation.name)
		self.select_button.setCheckable(True)
		self.select_button.setFixedHeight(self.height)

		self.close_button = QPushButton("X")
		self.close_button.setFixedSize(self.height, self.height)

		layout.addWidget(self.select_button)
		layout.addWidget(self.close_button)

	def setChecked(self, checked: bool):
		self.select_button.setChecked(checked)

class ConversationPicker(QWidget):
	def __init__(self, button_height: int = 25):
		super().__init__()
		self.button_height = button_height
		self.init_ui()
		AppContext.context_changed.connect(self.on_context_changed)
		self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

	def init_ui(self):
		self.layout = QHBoxLayout(self)
		self.layout.setContentsMargins(0, 0, 0, 0)
		self.layout.setSpacing(1)
		self.layout.setAlignment(Qt.AlignLeft)

		self.scroll_area = QScrollArea()
		self.scroll_area.setWidgetResizable(True)
		self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
		self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
		
		self.scroll_content = QWidget()
		self.scroll_layout = QHBoxLayout(self.scroll_content)
		self.scroll_layout.setContentsMargins(0, 0, 0, 0)
		self.scroll_layout.setSpacing(1)
		self.scroll_layout.setAlignment(Qt.AlignLeft)

		self.scroll_area.setWidget(self.scroll_content)
		self.layout.addWidget(self.scroll_area)
	
	@run_in_main_thread
	def on_context_changed(self):
		self.update_tabs()
		
	def update_tabs(self):
		# Clear existing tabs
		while self.scroll_layout.count():
			child = self.scroll_layout.takeAt(0)
			if child.widget():
				child.widget().deleteLater()

		# Create new tabs for each active conversation
		for conversation in AppContext.active_conversations:
			if conversation is None:
				continue
			tab = ConversationTab(conversation, self.button_height)
			tab.select_button.clicked.connect(lambda _, c=conversation: self.on_conversation_select(c))
			tab.close_button.clicked.connect(lambda _, c=conversation: self.on_conversation_close(c))
			tab.setChecked(conversation == AppContext.conversation)
			self.scroll_layout.addWidget(tab)
			self.scroll_layout.addSpacing(5)

		self.scroll_layout.addStretch(1)
		self.update()

	def on_conversation_select(self, conversation: Conversation):
		AppContext.conversation = conversation
		self.update_tabs()

	def on_conversation_close(self, conversation: Conversation):
		if conversation in AppContext.active_conversations:
			index = AppContext.active_conversations.index(conversation)
			AppContext.active_conversations.remove(conversation)
			
			if conversation == AppContext.conversation:
				if AppContext.active_conversations:
					if index < len(AppContext.active_conversations):
						AppContext.conversation = AppContext.active_conversations[index]
					else:
						AppContext.conversation = AppContext.active_conversations[index - 1]
				else:
					AppContext.conversation = None
			
			AppContext.context_changed()

	def resizeEvent(self, event):
		super().resizeEvent(event)
		self.updateGeometry()

	def sizeHint(self):
		width = self.minimumWidth()
		height = self.button_height
		if self.scroll_area.horizontalScrollBar().isVisible():
			height += self.scroll_area.horizontalScrollBar().height()
		return QSize(width, height + 2)

	def minimumSizeHint(self):
		return self.sizeHint()

	def minimumWidth(self):
		if self.layout.count() > 0:
			first_item = self.layout.itemAt(0)
			if first_item and first_item.widget():
				return first_item.widget().sizeHint().width()
		return 0

# Usage example:
if __name__ == "__main__":
	from PyQt5.QtWidgets import QApplication, QMainWindow
	import sys

	class MainWindow(QMainWindow):
		def __init__(self):
			super().__init__()
			self.conversation_picker = ConversationPicker()
			self.setCentralWidget(self.conversation_picker)

			# Add some test conversations
			for i in range(5):
				AppContext.active_conversations.append(Conversation(f"Conversation {i+1}", f"Description {i+1}"))

			AppContext.context_changed()

	app = QApplication(sys.argv)
	main_window = MainWindow()
	main_window.show()
	sys.exit(app.exec_())