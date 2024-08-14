from PyQt5.QtWidgets import QWidget, QHBoxLayout, QPushButton, QScrollArea, QSizePolicy
from PyQt5.QtCore import Qt, QSize
from AbstractAI.UI.Context import Context
from AbstractAI.Model.Converse import Conversation

class ConversationButton(QPushButton):
	def __init__(self, conversation: Conversation):
		super().__init__(conversation.name)
		self.conversation = conversation
		self.setCheckable(True)
		self.setToolTip(conversation.description)

class ConversationPicker(QWidget):
	def __init__(self, button_height: int = 25):
		super().__init__()
		self.button_height = button_height
		self.init_ui()
		Context.context_changed.connect(self.update_buttons)
		self.update_buttons()

	def init_ui(self):
		self.setStyleSheet("background-color: 255,255,255;")
		main_layout = QHBoxLayout(self)
		main_layout.setContentsMargins(0, 0, 0, 0)

		self.scroll_area = QScrollArea(self)
		self.scroll_area.setWidgetResizable(True)
		self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
		self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

		self.content_widget = QWidget()
		self.layout = QHBoxLayout(self.content_widget)
		self.layout.setSpacing(10)  # Space between conversation groups
		self.layout.setContentsMargins(0, 0, 0, 0)
		self.layout.setAlignment(Qt.AlignLeft)  # Align buttons to the left
		self.scroll_area.setFrameShape(QScrollArea.NoFrame)
		self.scroll_area.setWidget(self.content_widget)
		main_layout.addWidget(self.scroll_area)

		self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

	def update_buttons(self):
		# Clear existing buttons
		while self.layout.count():
			child = self.layout.takeAt(0)
			if child.widget():
				child.widget().deleteLater()

		# Create new buttons for each active conversation
		for conversation in Context.active_conversations:
			group = QWidget()
			group_layout = QHBoxLayout(group)
			group_layout.setSpacing(0)
			group_layout.setContentsMargins(0, 0, 0, 0)

			button = ConversationButton(conversation)
			button.setFixedHeight(self.button_height)
			button.setChecked(conversation == Context.conversation)
			button.clicked.connect(self.on_conversation_button_clicked)

			close_button = QPushButton("X")
			close_button.setFixedSize(20, self.button_height)
			close_button.clicked.connect(lambda _, c=conversation: self.close_conversation(c))

			group_layout.addWidget(button)
			group_layout.addWidget(close_button)

			self.layout.addWidget(group)

		self.layout.addStretch(1)  # Add stretch at the end to keep buttons left-aligned
		self.adjustSize()
		self.update()

	def on_conversation_button_clicked(self):
		button = self.sender()
		if button.isChecked():
			Context.conversation = button.conversation
			self.update_buttons()

	def close_conversation(self, conversation: Conversation):
		if conversation in Context.active_conversations:
			index = Context.active_conversations.index(conversation)
			Context.active_conversations.remove(conversation)

			if conversation == Context.conversation:
				if Context.active_conversations:
					Context.conversation = Context.active_conversations[min(index, len(Context.active_conversations) - 1)]
				else:
					Context.conversation = None

			Context.context_changed()

	def resizeEvent(self, event):
		super().resizeEvent(event)
		self.updateGeometry()

	def sizeHint(self):
		width = self.minimumWidth()
		height = self.button_height
		if self.scroll_area.horizontalScrollBar().isVisible():
			height += self.scroll_area.horizontalScrollBar().height()
		return QSize(width, height)

	def minimumSizeHint(self):
		return self.sizeHint()

	def minimumWidth(self):
		if self.layout.count() > 0:
			first_item = self.layout.itemAt(0)
			if first_item and first_item.widget():
				return first_item.widget().sizeHint().width()
		return 0