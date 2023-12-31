from .ConversationView import ConversationView
from .RoleComboBox import RoleComboBox

class ChatUI(QWidget):
	#qt signal for sending messages
	message_added = pyqtSignal(Conversation, Message, bool)
	message_changed = pyqtSignal(Message, str) # Message, old hash
	confirm_command = pyqtSignal()
	
	
	def __init__(self, db:ConversationDB, conversation: Conversation, roles:List[str], max_new_message_lines=5):
		super().__init__()
		
		self.db = db
		self.conversation = conversation
		self.roles = roles
		
		self.max_new_message_lines = max_new_message_lines
		self.num_lines = 0
		
		self.init_ui()
		self.has_unrun_command = False
		
		self.read_settings()
		
	def init_ui(self):
		self.setWindowTitle('Chat')

		self.layout = QVBoxLayout()
		self.setLayout(self.layout)
		
		# Create a labeled text field to enter the startup command for the conversation:
		self.startup_command_layout = QHBoxLayout()
		self.startup_command_label = QLabel("Startup Command:")
		self.startup_command_layout.addWidget(self.startup_command_label)
		self.startup_command_field = QLineEdit()
		self.startup_command_field.setText(self.db.get_conversation_startup_script(self.conversation))
		self.startup_command_field.textChanged.connect(self.startup_command_changed)
		self.startup_command_layout.addWidget(self.startup_command_field)
		self.layout.addLayout(self.startup_command_layout)
		
		# Add a clear all button:
		self.clear_all_button = QPushButton("Clear All")
		self.clear_all_button.clicked.connect(self.clear_all)
		self.startup_command_layout.addWidget(self.clear_all_button)
		
		# Create a list view to display the conversation:
		self.list_view = ConversationView(self.conversation)
		self.list_view.message_changed.connect(self.message_changed.emit)
		self.layout.addWidget(self.list_view)
		
		# Create a text field to enter new messages:
		self.input_layout = QHBoxLayout()
		self.role_combobox = RoleComboBox(self.roles, default_value="Human")
		self.input_layout.addWidget(self.role_combobox, alignment=Qt.AlignBottom)

		self.input_field = QTextEdit()
		size_policy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
		size_policy.setVerticalStretch(1)
		self.input_field.setSizePolicy(size_policy)
		self.input_field.setMaximumHeight(self.input_field.fontMetrics().lineSpacing())
		self.input_field.setWordWrapMode(QTextOption.WrapAtWordBoundaryOrAnywhere)
		self.input_field.textChanged.connect(self.adjust_input_field_size)
		self.input_field.textChanged.connect(self.update_send_button_text)
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
		settings = QSettings("MyCompany", "MyApp")
		settings.setValue("geometry", self.saveGeometry())
		
	def send_message(self):
		message = None
		
		message_text = self.input_field.toPlainText()
		message = Message.from_role_content(self.role_combobox.currentText(), message_text)
			
		self.message_added.emit(
			self.conversation, 
			message,
			self.send_add_toggle.isChecked()
		)
		
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
	
	def render_message(self, message:Message):
		self.list_view.render_message(message)
	
	def update_send_button_text(self):
		#"Run" if has unrun command, change to run, and the input field is empty:
		if self.has_unrun_command and self.input_field.toPlainText() == "":
			if self.send_button.text() != "Run":
				self.send_button.setText("Run")
				try:
					self.send_button.clicked.disconnect(self.send_message)
				except TypeError:
					pass
				self.send_button.clicked.connect(self.confirm_command.emit)
		else:
			if self.send_button.text() == "Run":
				try:
					self.send_button.clicked.disconnect(self.confirm_command.emit)
				except TypeError:
					pass
				self.send_button.clicked.connect(self.send_message)
			self.send_button.setText("Send" if self.send_add_toggle.isChecked() else "Add")
	
	@property
	def has_unrun_command(self):
		return self._has_unrun_command
	
	@has_unrun_command.setter
	def has_unrun_command(self, value:bool):
		self._has_unrun_command = value
		self.update_send_button_text()
		
	def startup_command_changed(self, text):
		self.db.set_conversation_startup_script(self.conversation, text)
	
	def clear_all(self):		
		message_box = QMessageBox()
		message_box.setIcon(QMessageBox.Question)
		message_box.setText("Are you sure you wish to clear the conversation? All conversations are in the db but theres currently no way to load them in the UI.")
		message_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)

		result = message_box.exec_()

		if result == QMessageBox.Yes:
			self.conversation.clear()
			self.list_view.clear()
		else:
			pass