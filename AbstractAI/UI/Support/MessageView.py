from .ColoredFrame import ColoredFrame
from AbstractAI.Conversation.Message import Message, Role, UserSource

class MessageView(ColoredFrame):
	rowHeightChanged = pyqtSignal()
	message_changed = pyqtSignal(Message, str) # Message, old hash
	
	def __init__(self, message: Message, parent=None):
		background_color = QColor( parent.color_palette.get(message.full_role.lower(), QColor(Qt.white)) )
		super().__init__(background_color, parent)
		
		self.parent = parent
		self.message = message
		
		self.layout = QHBoxLayout()
		self.setLayout(self.layout)
		
		self.left_layout = QVBoxLayout()
		self.layout.addLayout(self.left_layout)
		
		# Role (and optional name) label
		self.role_label = QLabel()
		#Get the role from the message, capitalizing the first letter of each word:
		pascal_role = " ".join([word.capitalize() for word in message.full_role.split(" ")])
		self.role_label.setText(f"{pascal_role}:")
		self.role_label.setFixedWidth(100)
		self.role_label.setWordWrap(True)
		self.left_layout.addWidget(self.role_label)
		
		# Date label
		self.date_label = QLabel()
		self.date_label.setText(message.date.strftime("%Y-%m-%d %H:%M:%S"))
		self.date_label.setFixedWidth(100)
		self.date_label.setWordWrap(True)
		self.left_layout.addWidget(self.date_label)
		
		# Token count label
		self.token_count_label = QLabel()
		self.token_count_label.setText(f"{tokens_in_message(message)} tokens")
		self.token_count_label.setFixedWidth(100)
		self.token_count_label.setWordWrap(True)
		self.left_layout.addWidget(self.token_count_label)
		
		# Should send toggle
		self.should_send_checkbox = QCheckBox("Send")
		self.should_send_checkbox.setChecked(message.should_send)
		self.should_send_checkbox.stateChanged.connect(self.on_should_send_changed)
		self.left_layout.addWidget(self.should_send_checkbox)
		
		# Spacer
		self.left_layout.addStretch()
		
		# Editable text box
		self.text_edit = QTextEdit()
		self.text_edit.setPlainText(message['content'])
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
		self.delete_btn.clicked.connect(lambda: self.parent.delete_message(self))
		
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
		# self.parent.message_changed.emit(self.message)
	
	def update_text_edit_height(self):
		new_height = int(self.delete_btn.sizeHint().height() * 3)
		margins = self.text_edit.contentsMargins()
		if self.expand_btn.arrowType() == Qt.DownArrow:
			new_height = max(int(self.text_edit.document().size().height()), new_height) + margins.top() + margins.bottom()
			self.text_edit.setFixedHeight(new_height)
		else:
			new_height = int(self.delete_btn.sizeHint().height() * 3) + margins.top() + margins.bottom()
			self.text_edit.setFixedHeight(new_height)
		self.rowHeightChanged.emit()
		
	def toggle_expand(self, checked):
		self.expand_btn.setArrowType(Qt.DownArrow if checked else Qt.RightArrow)
		self.update_text_edit_height()
		
	def on_text_changed(self):
		text = self.text_edit.toPlainText()
		if text != self.message['content']:
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
		
		self.token_count_label.setText(f"{tokens_in_string(text)} tokens")
		
	def delete_message(self):
		pass

	def confirm_changes(self):
		old_hash = self.message.hash
		self.message.json['content'] = self.text_edit.toPlainText()
		self.confirm_btn.setVisible(False)
		self.text_edit.setStyleSheet("")
		self.message.recompute_hash()
		
		self.message_changed.emit(self.message, old_hash)

