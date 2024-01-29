from .ConversationView import ConversationView
from .RoleComboBox import RoleComboBox
from AbstractAI.UI.Support._CommonImports import *
from AbstractAI.ConversationModel import *

#TODO: this needs to be more compatible with tool use, break it up to include or not include a send button, vs cancel accept buttons, etc.

#TODO: this should hold the info to create a model source but should pass things up out of it and should itself be a chat view not directly tied to a model
class ChatUI(QWidget):
	confirm_command = pyqtSignal()
	
	def __init__(self, conversation: Conversation, roles:List[str]=["Human", "Terminal", "Assistant"], max_new_message_lines=5):
		super().__init__()
		
		self.conversation = conversation
		self.roles = roles #TODO: Change role strings for chat
		
		self.max_new_message_lines = max_new_message_lines
		self.num_lines = 0
		
		self.init_ui()
		
		self.read_settings()
		
	def init_ui(self):
		self.layout = QVBoxLayout()
		self.setLayout(self.layout)
		
		# Create a list view to display the conversation:
		self.conversation_view = ConversationView(self.conversation)
		self.layout.addWidget(self.conversation_view)
		
		# Create a text field to enter new messages:
		self.input_layout = QHBoxLayout()
		self.role_combobox = RoleComboBox(self.roles, default_value=self.roles[0])
		self.input_layout.addWidget(self.role_combobox, alignment=Qt.AlignBottom)

		self.input_field = QTextEdit()
		size_policy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
		size_policy.setVerticalStretch(1)
		self.input_field.setSizePolicy(size_policy)
		self.input_field.setMaximumHeight(self.input_field.fontMetrics().lineSpacing())
		self.input_field.setWordWrapMode(QTextOption.WrapAtWordBoundaryOrAnywhere)
		self.input_field.textChanged.connect(self.adjust_input_field_size)
		self.input_field.setPlaceholderText("Type your message here...")
		self.input_layout.addWidget(self.input_field, alignment=Qt.AlignBottom)
		
		# Create a button to send the message:
		self.send_button = QPushButton('Send')
		self.send_button.clicked.connect(self.send_message)
		
		self.send_add_toggle = QCheckBox()
		self.send_add_toggle.setCheckState(Qt.Checked)
		self.send_add_toggle.stateChanged.connect(lambda: self.update_send_button_text())
		self.input_layout.addWidget(self.send_add_toggle, alignment=Qt.AlignBottom)
		
		self.input_layout.addWidget(self.send_button, alignment=Qt.AlignBottom)
		
		self.layout.addLayout(self.input_layout)
		self.input_field.setMinimumHeight(self.send_button.sizeHint().height())
		
		# Set the chat text box as selected:
		self.input_field.setFocus()
		
	def read_settings(self):
		settings = QSettings("MyCompany", "MyApp")
		self.restoreGeometry(settings.value("geometry", QByteArray()))

	def write_settings(self):
		settings = QSettings("MyCompany", "MyApp") #TODO: Move settings to the main window to be and add which conv was open as well as what more (columns, tabs, or windows) the ui is in
		settings.setValue("geometry", self.saveGeometry())
		
	def send_message(self):
		new_message = Message(self.input_field.toPlainText())
		selected_role = self.role_combobox.currentText()
		if selected_role == "Human":
			new_message.source = UserSource()
		elif selected_role == "Terminal":
			new_message.source = TerminalSource()
		elif selected_role == "Assistant":
			new_message.source = ModelSource()
		self.conversation.add_message(new_message)
		self.input_field.clear()
		
	def closeEvent(self, event):
		self.write_settings()
		super().closeEvent(event)
		
	def keyPressEvent(self, event):
		if event.key() == Qt.Key_Enter and event.modifiers() == Qt.ControlModifier:
			self.send_button.click()
		else:
			super().keyPressEvent(event)
	
	def adjust_input_field_size(self):
		"""Adjust the height of the input field to fit the text up to max lines"""
		n_lines = self.input_field.document().blockCount()
		lines_to_show = min(n_lines, self.max_new_message_lines)
		new_height = self.input_field.fontMetrics().lineSpacing() * lines_to_show + 10
		self.input_field.setMaximumHeight(int(new_height))

		if n_lines >= self.max_new_message_lines:
			self.input_field.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
		else:
			self.input_field.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
			
		self.input_field.updateGeometry()
		
		if self.num_lines < n_lines:
			self.input_field.verticalScrollBar().setValue(self.input_field.verticalScrollBar().maximum())
		self.num_lines = n_lines
	
	def set_conversation(self, conversation: Conversation):
		self.conversation = conversation
		self.conversation_view.set_conversation(conversation)