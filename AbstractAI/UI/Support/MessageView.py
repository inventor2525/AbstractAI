from .ColoredFrame import *
from AbstractAI.ConversationModel.Message import Message
from AbstractAI.ConversationModel.MessageSources import *
from .MessageSourceView import MessageSourceView
from .RoleColorPallet import RoleColorPallet

message_color_pallet = RoleColorPallet()
class BaseMessageView(ColoredFrame):
	def __init__(self, background_color, parent, message: Message):
		super().__init__(background_color, parent)
		self._message = message
		
class MessageView(BaseMessageView):
	rowHeightChanged = pyqtSignal()
	
	# Signal fired when a message change is confirmed by the user, passes the new message
	message_changed = pyqtSignal(Message)
	
	# Signal fired when a message is deleted by the user, passes the message view to be deleted
	message_deleted_clicked = pyqtSignal(BaseMessageView)
	
	def __init__(self, message: Message, parent=None):
		background_color = message_color_pallet.get_color(self._origional_source(message.source))
		super().__init__(background_color, parent, message)
		
		self.parent = parent
		
		self.layout = QHBoxLayout()
		self.setLayout(self.layout)
		
		self.left_layout = QVBoxLayout()
		self.layout.addLayout(self.left_layout)
		
		self.message_source_view = MessageSourceView(message.source)
		self.left_layout.addWidget(self.message_source_view)
		
		# Role (and optional name) label
		# self.role_label = QLabel()
		# #Get the role from the message, capitalizing the first letter of each word:
		# pascal_role = " ".join([word.capitalize() for word in message.full_role.split(" ")])
		# self.role_label.setText(f"{pascal_role}:")
		# self.role_label.setFixedWidth(100)
		# self.role_label.setWordWrap(True)
		# self.left_layout.addWidget(self.role_label)
		
		# Date label
		self.date_label = QLabel()
		self.date_label.setText(message.creation_time.strftime("%Y-%m-%d %H:%M:%S"))
		self.date_label.setFixedWidth(100)
		self.date_label.setWordWrap(True)
		self.left_layout.addWidget(self.date_label)
		
		# # Token count label
		# self.token_count_label = QLabel()
		# self.token_count_label.setText(f"{tokens_in_message(message)} tokens")
		# self.token_count_label.setFixedWidth(100)
		# self.token_count_label.setWordWrap(True)
		# self.left_layout.addWidget(self.token_count_label)
		
		# # Should send toggle
		# self.should_send_checkbox = QCheckBox("Send")
		# self.should_send_checkbox.setChecked(message.should_send)
		# self.should_send_checkbox.stateChanged.connect(self.on_should_send_changed)
		# self.left_layout.addWidget(self.should_send_checkbox)
		
		# Spacer
		self.left_layout.addStretch()
		
		# Horizontal layout for left and right arrow buttons
		self.arrow_layout = QHBoxLayout()
		
		# Left arrow button for selecting previous version of message:
		self.left_arrow_btn = QToolButton()
		self.left_arrow_btn.setArrowType(Qt.LeftArrow)
		self.left_arrow_btn.setFixedHeight(15)
		self.left_arrow_btn.setFixedWidth(15)
		def left_arrow_clicked():
			self.message.conversation.update_message_graph()
			if self.message.prev_message is not None:
				index = self.message.prev_message._children.index(self.message)-1
				if index < 0:
					index = 0
				self.message = self.message.prev_message._children[index]
				
		self.left_arrow_btn.clicked.connect(left_arrow_clicked)
		
		# Right arrow button for selecting next version of message:
		self.right_arrow_btn = QToolButton()
		self.right_arrow_btn.setArrowType(Qt.RightArrow)
		self.right_arrow_btn.setFixedHeight(15)
		self.right_arrow_btn.setFixedWidth(15)
		def right_arrow_clicked():
			self.message.conversation.update_message_graph()
			if self.message.prev_message is not None:
				index = self.message.prev_message._children.index(self.message)+1
				if index >= len(self.message.prev_message._children):
					index = len(self.message.prev_message._children)-1
				self.message = self.message.prev_message._children[index]
		self.right_arrow_btn.clicked.connect(right_arrow_clicked)
		
		# create another 2 buttons to the left of the left and
		# right of the right that also swap the children out:
		# TODO: make these buttons work
		# TODO: track the changes in the message sequence and have proper notifications
		
		self.arrow_layout.addWidget(self.left_arrow_btn)
		self.arrow_layout.addWidget(self.right_arrow_btn)
		
		self.left_layout.addLayout(self.arrow_layout)
		
		# Editable text box
		self.text_edit = QTextEdit()
		self.text_edit.setPlainText(message.content)
		self.text_edit.setLineWrapMode(QTextEdit.WidgetWidth)
		self.text_edit.setWordWrapMode(QTextOption.WrapAtWordBoundaryOrAnywhere)
		self.text_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
		self.text_edit.textChanged.connect(self.on_text_changed)
		self.text_edit.textChanged.connect(self.update_text_edit_height)
		self.layout.addWidget(self.text_edit)

		# Vertical panel
		self.panel_layout = QVBoxLayout()
		self.panel_layout.setAlignment(Qt.AlignTop)
		self.layout.addLayout(self.panel_layout)

		# Delete button (X)
		self.delete_btn = QPushButton("X")
		self.delete_btn.clicked.connect(self.delete_message)
		self.delete_btn.setFixedWidth(25)
		self.panel_layout.addWidget(self.delete_btn, alignment=Qt.AlignTop)
		self.delete_btn.clicked.connect(lambda: self.message_deleted_clicked.emit(self))
		
		# Confirm button (checkmark)
		self.confirm_btn = QPushButton("✓")
		self.confirm_btn.clicked.connect(self.confirm_changes)
		self.confirm_btn.setVisible(False)
		self.confirm_btn.setFixedWidth(25)
		self.panel_layout.addWidget(self.confirm_btn, alignment=Qt.AlignTop)

		# Expand message view button (rotating arrow)
		self.expand_btn = QToolButton()
		self.expand_btn.setCheckable(True)
		self.expand_btn.setArrowType(Qt.RightArrow)
		self.expand_btn.toggled.connect(self.toggle_expand)
		self.panel_layout.addWidget(self.expand_btn, alignment=Qt.AlignTop)

		self.update_text_edit_height()
	
	def on_should_send_changed(self, state):
		self.message.should_send = state == Qt.Checked
	
	def update_text_edit_height(self):
		margins = self.text_edit.contentsMargins()
		
		new_height = max(
			int(self.panel_layout.sizeHint().height()),
			int(self.left_layout.sizeHint().height())
		)
		def set_height(new_height):
			self.text_edit.setFixedHeight(new_height + margins.top() + margins.bottom())
			
		if self.expand_btn.arrowType() == Qt.DownArrow:
			set_height(max(new_height, int(self.text_edit.document().size().height())))
		else:
			set_height(new_height)
		self.rowHeightChanged.emit()
		
	def toggle_expand(self, checked):
		self.expand_btn.setArrowType(Qt.DownArrow if checked else Qt.RightArrow)
		self.update_text_edit_height()
		
	def on_text_changed(self):
		text = self.text_edit.toPlainText()
		if text != self.message.content:
			self.confirm_btn.setVisible(True)
			# self.text_edit.setStyleSheet("border: 3px solid rgba(0, 0, 255, 0.3);")
			self.text_edit.setStyleSheet("QTextEdit {border: 3px solid rgba(0, 0, 255, 0.3);}")

		else:
			self.confirm_btn.setVisible(False)
			self.text_edit.setStyleSheet("")
			
		if self.expand_btn.isChecked():
			self.text_edit.setMinimumHeight(int(self.text_edit.document().size().height()))
			self.text_edit.updateGeometry()
			self.rowHeightChanged.emit()
		
		# self.token_count_label.setText(f"{tokens_in_string(text)} tokens")
		
	def delete_message(self):
		self.message_deleted_clicked.emit(self)

	def confirm_changes(self):
		self.message = self.message.create_edited(self.text_edit.toPlainText())
		
		self.message_changed.emit(self.message)
	
	def _origional_source(self, source:MessageSource):
		if isinstance(source, EditSource):
			source = EditSource.most_original(source).source
		return source
	
	@property
	def message(self):
		return self._message
	@message.setter
	def message(self, value:Message):
		self._message = value
		
		self.message_source_view.set_message_source(value.source)
		self.confirm_btn.setVisible(False)
		
		# self.role_label.setText(f"{value.full_role}:")
		# self.token_count_label.setText(f"{tokens_in_message(value)} tokens")
		
		self.text_edit.setPlainText(value.content)
		self.text_edit.setStyleSheet("")
		self.update_text_edit_height()
		
		self.date_label.setText(value.creation_time.strftime("%Y-%m-%d %H:%M:%S"))
		
		# self.should_send_checkbox.setChecked(value.should_send)
		
		self.background_color = message_color_pallet.get_color(self._origional_source(value.source))
		self.update()