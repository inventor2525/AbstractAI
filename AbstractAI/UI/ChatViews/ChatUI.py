from AbstractAI.UI.Elements.TextEdit import TextEdit
from AbstractAI.UI.ChatViews.ConversationView import ConversationView
from AbstractAI.UI.ChatViews.MessageView_extras.RoleComboBox import RoleComboBox
from AbstractAI.UI.Support._CommonImports import *
from AbstractAI.UI.Context import Context
from AbstractAI.ConversationModel import *
from AbstractAI.Helpers.log_caller_info import log_caller_info
from PyQt5.QtCore import QTimer

class ChatUI(QWidget):
	user_added_message = pyqtSignal(Conversation)
	stop_generating = pyqtSignal()
	
	@property
	def conversation(self) -> Conversation:
		return self.conversation_view.conversation
	@conversation.setter
	def conversation(self, value:Conversation):
		self.conversation_view.conversation = value
	
	@property
	def message_prefix(self) -> str:
		return self.message_prefix_field.toPlainText()
	
	def __init__(self, conversation: Conversation = None, roles:List[str]=["Human", "Assistant", "System"], max_new_message_lines=10):
		super().__init__()		
		self.roles = roles
		
		self.role_source_map = {
			"Human": UserSource(),
			"Assistant": ModelInfo("ChatUI", "Impersonation", log_caller_info(except_keys=['instance_id'])),
			"System": SystemSource(),
		}
		
		self.max_new_message_lines = max_new_message_lines
		self.num_lines = 0
		
		self.init_ui(conversation)
		
	def init_ui(self, conversation:Conversation = None):
		self.layout = QVBoxLayout()
		self.layout.setContentsMargins(0, 0, 0, 0)
		self.setLayout(self.layout)
		
		# Create a list view to display the conversation:
		self.conversation_view = ConversationView(conversation)
		self.conversation_view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
		self.layout.addWidget(self.conversation_view)
		
		# Create a layout to hold the user input and send button:
		self.input_layout = QHBoxLayout()
		self.layout.addLayout(self.input_layout)
		
		# Create a layout to hold the advanced controls:
		self.advanced_controls = QWidget()
		self.advanced_controls.setContentsMargins(0, 0, 0, 0)
		self.advanced_controls_layout = QVBoxLayout()
		self.advanced_controls.setLayout(self.advanced_controls_layout)
		self.layout.addWidget(self.advanced_controls)
		
		self.message_prefix_field = TextEdit("AI message prefix field", auto_save=True)
		size_policy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
		self.message_prefix_field.setSizePolicy(size_policy)
		self.message_prefix_field.setWordWrapMode(QTextOption.WrapAtWordBoundaryOrAnywhere)
		self.message_prefix_field.setPlaceholderText("Type the start of the ai message here...")
		self.advanced_controls_layout.addWidget(self.message_prefix_field)
		
		# Allow the user to select a role to send the message as:
		self.role_combobox = RoleComboBox(self.roles, default_value=self.roles[0])
		self.input_layout.addWidget(self.role_combobox, alignment=Qt.AlignBottom)
		
		# Create a text box to type the message:
		self.input_field = TextEdit("New Message Input Field", auto_save=True)
		self.input_field.setWordWrapMode(QTextOption.WrapAtWordBoundaryOrAnywhere)
		self.input_field.textChanged.connect(self.adjust_input_field_size)
		self.input_field.setPlaceholderText("Type your message here...")
		self.input_field.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
		self.input_layout.addWidget(self.input_field, alignment=Qt.AlignBottom)
		self.input_field.setFocus()
		
		# Create a button to toggle whether the chat should be processed by the model on send:
		self.respond_on_send_toggle = QToolButton()
		self.respond_on_send_toggle.setCheckable(True)
		self.respond_on_send_toggle.setChecked(True)
		self.respond_on_send_toggle.setText("Auto Respond")
		self.respond_on_send_toggle.setToolTip("Automatically respond to this message")
		self.respond_on_send_toggle.clicked.connect(lambda: self.update_send_button_text())
		self.input_layout.addWidget(self.respond_on_send_toggle, alignment=Qt.AlignBottom)
		
		# Create a button to toggle the advanced controls:
		self.advanced_controls_toggle = QToolButton()
		self.advanced_controls_toggle.setCheckable(True)
		self.advanced_controls_toggle.setChecked(Context.settings.value("ChatUI/ShowAdvancedControls", False, type=bool))
		# self.advanced_controls_toggle.setText("
		self.advanced_controls_toggle.setIcon(QIcon.fromTheme("preferences-system"))
		self.advanced_controls_toggle.setToolTip("Show advanced controls")
		def toggle_advanced_controls():
			Context.settings.setValue("ChatUI/ShowAdvancedControls", self.advanced_controls_toggle.isChecked())
			self.advanced_controls.setVisible(self.advanced_controls_toggle.isChecked())
		self.advanced_controls_toggle.clicked.connect(toggle_advanced_controls)
		self.input_layout.addWidget(self.advanced_controls_toggle, alignment=Qt.AlignBottom)
		toggle_advanced_controls()
		
		# Create a button to send the message:
		# This is a multi-use button that can be used to send a message, 
		# add it, or stop the generation of a message:
		self.send_button = QPushButton('Send Msg')
		self.send_button.clicked.connect(self.send_message)
		self.input_layout.addWidget(self.send_button, alignment=Qt.AlignBottom)
		
		# Adjust the size of the bottom row to fit the input field:
		self.adjust_input_field_size()
		self.advanced_controls_toggle.setFixedHeight(self.input_field.height())
		self.respond_on_send_toggle.setFixedHeight(self.input_field.height())
		self.send_button.setFixedHeight(self.input_field.height())
		self.role_combobox.setFixedHeight(self.input_field.height())
		
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
			self.send_button.setText("Send Msg")
		else:
			self.send_button.setText("Add Msg")
			
	def change_to_stop(self):
		try:
			self.send_button.clicked.disconnect(self.send_message)
			self.send_button.clicked.connect(self._stop_generating)
		except:
			pass
		self.send_button.setText("Stop!")
		
	def change_to_send(self):
		try:
			self.send_button.clicked.disconnect(self._stop_generating)
			self.send_button.clicked.connect(self.send_message)
		except:
			pass
		self.update_send_button_text()
		
	def _stop_generating(self):
		self.stop_generating.emit()
		self.change_to_send()
		
	def keyPressEvent(self, event):
		if event.key() == Qt.Key_Enter and event.modifiers() == Qt.ControlModifier:
			self.send_button.click()
		else:
			super().keyPressEvent(event)
	
	def adjust_input_field_size(self):
		"""Adjust the height of the input field to fit the text up to max lines"""
		content_height = self.input_field.document().size().height()
		content_margin_sum = + self.input_field.contentsMargins().top() + self.input_field.contentsMargins().bottom()
		
		max_height = self.input_field.fontMetrics().lineSpacing()*self.max_new_message_lines + self.input_field.document().documentMargin()*2
		
		new_height = min(content_height, max_height) + content_margin_sum
		self.input_field.setFixedHeight(int(new_height))