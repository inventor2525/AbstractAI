from AbstractAI.UI.Elements.TextEdit import TextEdit
from AbstractAI.UI.ChatViews.ConversationView import ConversationView
from AbstractAI.UI.ChatViews.MessageView_extras.RoleComboBox import RoleComboBox
from AbstractAI.UI.ChatViews.ConversationActionControl import ConversationActionControl, ConversationAction
from AbstractAI.UI.Support._CommonImports import *
from AbstractAI.UI.Context import Context
from AbstractAI.Model.Converse import *
from AbstractAI.Model.Converse.MessageSources.FilesSource import ItemsModel
from AbstractAI.UI.Elements.FileSelector import FileSelectionWidget
from copy import deepcopy

class ChatUI(QWidget):
	respond_to_conversation = pyqtSignal(Conversation)
	stop_generating = pyqtSignal()
	
	@property
	def conversation(self) -> Conversation:
		return self.conversation_view.conversation
	@conversation.setter
	def conversation(self, value:Conversation):
		self.conversation_view.conversation = value
	
	@property
	def start_str(self) -> str:
		return self.message_prefix_field.toPlainText()
	
	@property
	def max_tokens(self) -> Optional[int]:
		try:
			return int(self.max_tokens_field.toPlainText())
		except:
			self.max_tokens_field.setText("")
			None
	
	def __init__(self, conversation: Conversation = None, roles:List[str]=["Human", "Assistant", "System", "Files"], max_new_message_lines=10):
		super().__init__()		
		self.roles = roles
		self.roles_map = {
			"Human":Role.User(),
			"Assistant":Role.Assistant(),
			"System":Role.System(),
			"Files":Role.User()
		}
		
		self.caller = CallerInfo.catch([0,1])
		self.user_source = UserSource() | self.caller
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
		self.advanced_controls_layout = QVBoxLayout()
		self.advanced_controls_layout.setContentsMargins(0, 0, 0, 0)
		self.advanced_controls.setLayout(self.advanced_controls_layout)
		self.layout.addWidget(self.advanced_controls)
		self.advanced_controls_layout.addWidget(QLabel("Advanced Generation Controls:"))
		self.advanced_controls_layout.addWidget(QHLine())
		
		# Create a field to set the max tokens:
		self.message_prefix_field_h_layout = QHBoxLayout()
		self.message_prefix_field_h_layout.addWidget(QLabel("Max Tokens:"))
		self.max_tokens_field = TextEdit("Max Tokens Field", auto_save=True)
		self.max_tokens_field.setFixedHeight(25)
		self.max_tokens_field.setPlaceholderText("Max Tokens")
		self.message_prefix_field_h_layout.addWidget(self.max_tokens_field)
		self.advanced_controls_layout.addLayout(self.message_prefix_field_h_layout)
		
		# Create a field to set the message prefix:
		self.advanced_controls_layout.addWidget(QLabel("AI Message Prefix:"))
		self.message_prefix_field = TextEdit("AI message prefix field", auto_save=True)
		self.message_prefix_field.setWordWrapMode(QTextOption.WrapAtWordBoundaryOrAnywhere)
		self.message_prefix_field.setPlaceholderText("Type the start of the ai message here...")
		def adjust_advanced_controls_size():
			self.adjust_text_field_size(self.message_prefix_field)
			self.advanced_controls.setFixedHeight(self.advanced_controls_layout.sizeHint().height())
		self.message_prefix_field.textChanged.connect(adjust_advanced_controls_size)
		self.advanced_controls_layout.addWidget(self.message_prefix_field)
		adjust_advanced_controls_size()
		
		# Allow the user to select a role to send the message as:
		self.role_combobox = RoleComboBox(self.roles, default_value=self.roles[0])
		self.input_layout.addWidget(self.role_combobox, alignment=Qt.AlignBottom)
		
		# Create a text box to type the message:
		self.input_field = TextEdit("New Message Input Field", auto_save=True)
		self.input_field.setWordWrapMode(QTextOption.WrapAtWordBoundaryOrAnywhere)
		def input_field_changed():
			self.adjust_text_field_size(self.input_field)
			Context.new_message_has_text = bool(self.input_field.toPlainText())
			Context.context_changed()
		self.input_field.textChanged.connect(input_field_changed)
		self.input_field.textChanged.connect(self.clear_selection)
		self.input_field.setPlaceholderText("Type your message here...")
		self.input_field.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
		self.input_layout.addWidget(self.input_field, alignment=Qt.AlignBottom)
		self.input_field.setFocus()
		
		self.file_selector = FileSelectionWidget()
		self.input_layout.addWidget(self.file_selector)
		def role_changed():
			if self.role_combobox.currentText() == "Files":
				self.input_field.setHidden(True)
				self.file_selector.setHidden(False)
			else:
				self.input_field.setHidden(False)
				self.file_selector.setHidden(True)
		self.role_combobox.currentTextChanged.connect(role_changed)
		role_changed()
		
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
		
		self.action_control = ConversationActionControl()
		self.action_control.perform_action.connect(self.on_action)
		def selection_changed():
			self.action_control.selected_messages = self.conversation_view.selected_messages
			self.action_control.update_mode()
		self.conversation_view.selection_changed.connect(selection_changed)
		self.input_layout.addWidget(self.action_control, alignment=Qt.AlignBottom)
		
		# Adjust the size of the bottom row to fit the input field:
		self.adjust_text_field_size(self.input_field)
		self.advanced_controls_toggle.setFixedHeight(self.input_field.height())
		self.action_control.setFixedHeight(self.input_field.height())
		self.role_combobox.setFixedHeight(self.input_field.height())
	
	def clear_selection(self):
		self.conversation_view.clearSelection()
		
	def _create_message(self) -> Message:
		selected_role = self.role_combobox.currentText()
		new_message = Message(self.input_field.toPlainText())
		new_message.role = self.roles_map[selected_role]
		
		if selected_role == "Assistant":
			new_message | ModelSource(self.conversation.message_sequence) | self.caller
		elif selected_role == "Files":
			items = ItemsModel(items=deepcopy(self.file_selector.items))
			items.new_id()
			new_message | FilesSource(items=items) | self.caller
			new_message.content = new_message.source.load()
		else:
			new_message | self.user_source
		return new_message
	
	def _add_message(self):
		new_message = self._create_message()
		self.conversation.add_message(new_message)
		
		selected_role = self.role_combobox.currentText()
		if selected_role != "Files":
			self.input_field.clear()
		
	
	def on_action(self, action:ConversationAction):
		if action == ConversationAction.Add:
			self._add_message()
		elif action == ConversationAction.Insert:
			new_message = self._create_message()
			self.conversation.insert_message(new_message, self.conversation_view.selected_messages[0])
			self.input_field.clear()
			
		elif action == ConversationAction.Send:
			Context.start_str = self.start_str
			self._add_message()
			self.respond_to_conversation.emit(self.conversation)
		elif action == ConversationAction.Reply:
			Context.start_str = self.start_str
			self.respond_to_conversation.emit(self.conversation)
		elif action == ConversationAction.Continue:
			Context.start_str = self.conversation[-1].content
			self.conversation.remove_message(self.conversation[-1], silent=True)
			self.respond_to_conversation.emit(self.conversation)
			
		elif action == ConversationAction.Stop:
			self.stop_generating.emit()
			
		elif action == ConversationAction.Demo:
			raise NotImplementedError("Demo not implemented")
		elif action == ConversationAction.DoIt:
			raise NotImplementedError("DoIt not implemented")
	
	def keyPressEvent(self, event):
		if event.key() == Qt.Key_Enter and event.modifiers() == Qt.ControlModifier:
			self.send_button.click()
		else:
			super().keyPressEvent(event)
	
	def adjust_text_field_size(self, text_field:QTextEdit=None):
		"""Adjust the height of the input field to fit the text up to max lines"""
		content_height = max(text_field.document().size().height(), text_field.fontMetrics().lineSpacing()+text_field.document().documentMargin()*2)
		content_margin_sum = + text_field.contentsMargins().top() + text_field.contentsMargins().bottom()
		
		max_height = text_field.fontMetrics().lineSpacing()*self.max_new_message_lines + text_field.document().documentMargin()*2
		
		new_height = min(content_height, max_height) + content_margin_sum
		text_field.setFixedHeight(int(new_height))