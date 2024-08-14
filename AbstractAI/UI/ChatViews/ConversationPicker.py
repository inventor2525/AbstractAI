from PyQt5.QtWidgets import QWidget, QHBoxLayout, QPushButton, QScrollArea, QSizePolicy
from PyQt5.QtCore import Qt, QSize, pyqtSignal
from AbstractAI.UI.Context import Context
from AbstractAI.Model.Converse import Conversation

class ConversationTab(QWidget):
	clicked = pyqtSignal(Conversation)
	close_requested = pyqtSignal(Conversation)

	def __init__(self, conversation: Conversation, height: int):
		super().__init__()
		self.conversation = conversation
		self.height = height
		self.init_ui()

	def init_ui(self):
		layout = QHBoxLayout(self)
		layout.setContentsMargins(5, 0, 0, 0)
		layout.setSpacing(0)

		self.button = QPushButton(self.conversation.name)
		self.button.setCheckable(True)
		self.button.setFixedHeight(self.height)
		self.button.clicked.connect(lambda: self.clicked.emit(self.conversation))

		close_button = QPushButton("×")
		close_button.setFixedSize(self.height, self.height)
		close_button.clicked.connect(lambda: self.close_requested.emit(self.conversation))

		layout.addWidget(self.button)
		layout.addWidget(close_button)

	def setChecked(self, checked: bool):
		self.button.setChecked(checked)

class ConversationTabBar(QWidget):
	conversation_selected = pyqtSignal(Conversation)
	conversation_closed = pyqtSignal(Conversation)

	def __init__(self, button_height: int = 25):
		super().__init__()
		self.button_height = button_height
		self.init_ui()
		Context.context_changed.connect(self.update_tabs)

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

	def update_tabs(self):
		# Clear existing tabs
		for i in reversed(range(self.scroll_layout.count())):
			widget = self.scroll_layout.itemAt(i).widget()
			if widget:
				widget.deleteLater()

		# Create new tabs for each active conversation
		for conversation in Context.active_conversations:
			tab = ConversationTab(conversation, self.button_height)
			tab.clicked.connect(self.on_tab_clicked)
			tab.close_requested.connect(self.on_tab_close_requested)
			tab.setChecked(conversation == Context.conversation)
			self.scroll_layout.addWidget(tab)

		self.scroll_layout.addStretch(1)
		self.update()

	def on_tab_clicked(self, conversation: Conversation):
		Context.conversation = conversation
		self.conversation_selected.emit(conversation)
		self.update_tabs()

	def on_tab_close_requested(self, conversation: Conversation):
		if conversation in Context.active_conversations:
			Context.active_conversations.remove(conversation)
			if conversation == Context.conversation:
				if Context.active_conversations:
					Context.conversation = Context.active_conversations[-1]
				else:
					Context.conversation = None
			self.conversation_closed.emit(conversation)
			Context.context_changed()

	def resizeEvent(self, event):
		super().resizeEvent(event)
		self.updateGeometry()

	def sizeHint(self):
		width = self.minimumWidth()
		height = self.button_height
		if self.scroll_area.horizontalScrollBar().isVisible():
			height += self.scroll_area.horizontalScrollBar().height()
		return QSize(width, height+2)

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
			self.tab_bar = ConversationTabBar()
			self.setCentralWidget(self.tab_bar)

			# Add some test conversations
			for i in range(5):
				Context.active_conversations.append(Conversation(f"Conversation {i+1}", f"Description {i+1}"))

			Context.context_changed()

	app = QApplication(sys.argv)
	main_window = MainWindow()
	main_window.show()
	sys.exit(app.exec_())