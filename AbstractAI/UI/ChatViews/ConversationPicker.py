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
	def __init__(self):
		super().__init__()
		self.init_ui()
		Context.context_changed.connect(self.update_buttons)
		self.update_buttons()

	def init_ui(self):
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

		self.scroll_area.setWidget(self.content_widget)
		main_layout.addWidget(self.scroll_area)

		self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)

	def update_buttons(self):
		# Clear existing buttons
		for i in reversed(range(self.layout.count())):
			widget = self.layout.itemAt(i).widget()
			if widget:
				widget.deleteLater()

		# Create new buttons for each active conversation
		for conversation in Context.active_conversations:
			group = QWidget()
			group_layout = QHBoxLayout(group)
			group_layout.setSpacing(0)
			group_layout.setContentsMargins(0, 0, 0, 0)

			button = ConversationButton(conversation)
			button.setChecked(conversation == Context.conversation)
			button.clicked.connect(self.on_conversation_button_clicked)

			close_button = QPushButton("X")
			close_button.setFixedWidth(20)
			close_button.clicked.connect(lambda _, c=conversation: self.close_conversation(c))

			group_layout.addWidget(button)
			group_layout.addWidget(close_button)

			self.layout.addWidget(group)
		self.layout.addStretch()
		self.content_widget.adjustSize()
		self.updateGeometry()
		self.layout.update()
		self.update()

	def on_conversation_button_clicked(self):
		button = self.sender()
		if button.isChecked():
			Context.conversation = button.conversation
			self.update_buttons()

	def close_conversation(self, conversation: Conversation):
		index = Context.active_conversations.index(conversation)
		Context.active_conversations.remove(conversation)

		if conversation == Context.conversation:
			if index < len(Context.active_conversations):
				Context.conversation = Context.active_conversations[index]
			elif index > 0:
				Context.conversation = Context.active_conversations[index - 1]
			else:
				Context.conversation = None

		Context.context_changed()