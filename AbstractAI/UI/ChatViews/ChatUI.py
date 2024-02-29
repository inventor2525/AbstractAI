from AbstractAI.UI.Elements.TextEdit import TextEdit
from AbstractAI.UI.ChatViews.ConversationView import ConversationView
from AbstractAI.UI.ChatViews.MessageView_extras.RoleComboBox import RoleComboBox
from AbstractAI.UI.Support._CommonImports import *
from AbstractAI.ConversationModel import *
from AbstractAI.Helpers.log_caller_info import log_caller_info
#TODO: this needs to be more compatible with tool use, break it up to include or not include a send button, vs cancel accept buttons, etc.

#TODO: this should hold the info to create a model source but should pass things up out of it and should itself be a chat view not directly tied to a model
class ChatUI(QWidget):
	user_added_message = pyqtSignal(Conversation)
	stop_generating = pyqtSignal()
	
	@property
	def conversation(self) -> Conversation:
		return self.conversation_view.conversation
	@conversation.setter
	def conversation(self, value:Conversation):
		self.conversation_view.conversation = value
	
	def __init__(self, conversation: Conversation = None, roles:List[str]=["Human", "Assistant", "System"], max_new_message_lines=5):
		super().__init__()
		
		self.conversation_view = ConversationView(conversation)
		
		self.roles = roles
		
		self.role_source_map = {
			"Human": UserSource(),
			"Assistant": ModelInfo("ChatUI", "Impersonation", log_caller_info(except_keys=['instance_id'])),
			"System": SystemSource(),
		}
		
		self.max_new_message_lines = max_new_message_lines
		self.num_lines = 0
		
		self.init_ui()
		
	def init_ui(self):
		self.layout = QVBoxLayout()
		self.layout.setContentsMargins(0, 0, 0, 0)
		self.setLayout(self.layout)
		
		# Create a list view to display the conversation:
		self.layout.addWidget(self.conversation_view)
		
		# Create a text field to enter new messages:
		self.input_layout = QHBoxLayout()
		self.role_combobox = RoleComboBox(self.roles, default_value=self.roles[0])
		self.input_layout.addWidget(self.role_combobox, alignment=Qt.AlignBottom)

		self.input_field = TextEdit()
		size_policy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
		size_policy.setVerticalStretch(1)
		self.input_field.setSizePolicy(size_policy)
		self.input_field.setMaximumHeight(self.input_field.fontMetrics().lineSpacing())
		self.input_field.setWordWrapMode(QTextOption.WrapAtWordBoundaryOrAnywhere)
		self.input_field.textChanged.connect(self.adjust_input_field_size)
		self.input_field.setPlaceholderText("Type your message here...")
		self.input_field.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
		self.input_layout.addWidget(self.input_field, alignment=Qt.AlignBottom)
		
		# Create a button to send the message:
		self.send_button = QPushButton('Send')
		self.send_button.clicked.connect(self.send_message)
		
		self.respond_on_send_toggle = QCheckBox()
		self.respond_on_send_toggle.setCheckState(Qt.Checked)
		self.respond_on_send_toggle.stateChanged.connect(lambda: self.update_send_button_text())
		self.respond_on_send_toggle.clicked.connect(lambda: self.update_send_button_text())
		self.input_layout.addWidget(self.respond_on_send_toggle, alignment=Qt.AlignBottom)
		
		self.input_layout.addWidget(self.send_button, alignment=Qt.AlignBottom)
		
		self.layout.addLayout(self.input_layout)
		self.input_field.setMinimumHeight(self.send_button.sizeHint().height())
		
		# Set the chat text box as selected:
		self.input_field.setFocus()
		
	def send_message(self):
		selected_role = self.role_combobox.currentText()
		
		new_message = Message(self.input_field.toPlainText())
		if selected_role == "Assistant":
			new_message.source = ModelSource(self.role_source_map[selected_role], self.conversation.message_sequence)
		else:
			new_message.source = self.role_source_map[selected_role]
		
		self.conversation.add_message(new_message)
		
		self.input_field.clear()
		if self.respond_on_send_toggle.isChecked():
			self.change_to_stop()
			self.user_added_message.emit(self.conversation)
	
	def update_send_button_text(self):
		if self.respond_on_send_toggle.isChecked():
			self.send_button.setText("Send")
		else:
			self.send_button.setText("Add")
			
	def change_to_stop(self):
		try:
			self.send_button.clicked.disconnect(self.send_message)
			self.send_button.clicked.connect(self._stop_generating)
		except:
			pass
		self.send_button.setText("Stop")
		
	def change_to_send(self):
		try:
			self.send_button.clicked.disconnect(self._stop_generating)
			self.send_button.clicked.connect(self.send_message)
		except:
			pass
		self.send_button.setText("Send")
		
	def _stop_generating(self):
		# self.change_to_send()
		
		self.stop_generating.emit()
		
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