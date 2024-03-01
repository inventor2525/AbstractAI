from AbstractAI.UI.Support.ColoredFrame import *
from AbstractAI.UI.Elements.TextEdit import TextEdit
from AbstractAI.ConversationModel.Message import Message
from AbstractAI.ConversationModel.MessageSources import *
from AbstractAI.Helpers.run_in_main_thread import run_in_main_thread
from .MessageView_extras.MessageSourceView import MessageSourceView
from AbstractAI.UI.ChatViews.MessageView_extras.RoleColorPallet import RoleColorPallet
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QTextCursor

message_color_pallet = RoleColorPallet()
class BaseMessageView(ColoredFrame):
	def __init__(self, parent, message: Message):
		super().__init__(parent)
		self._message = message
		
class MessageView(BaseMessageView):
	rowHeightChanged = pyqtSignal()
	
	# Signal fired when a message change is confirmed by the user, passes the new message
	message_changed = pyqtSignal(Message)
	
	# Signal fired when a message is deleted by the user, passes the message view to be deleted
	message_deleted_clicked = pyqtSignal(BaseMessageView)
	
	regenerate_clicked = pyqtSignal(ModelSource)
	
	@property
	def editing(self) -> bool:
		return self._editing
	@editing.setter
	def editing(self, value:bool):
		self._editing = value
		self._update_edit_state()

	@property
	def edit_enabled(self) -> bool:
		return self._edit_enabled
	@edit_enabled.setter
	def edit_enabled(self, value:bool):
		self._edit_enabled = value
		self.text_edit.setReadOnly(not self._edit_enabled)
		if not self._edit_enabled:
			self.editing = False

	def __init__(self, message: Message, parent=None):
		super().__init__(parent, message)
		
		self.parent = parent
		self._editing = False
		self._edit_enabled = True

		self.layout = QHBoxLayout()
		self.setLayout(self.layout)
		
		self.left_layout = QVBoxLayout()
		self.layout.addLayout(self.left_layout)
		
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
		
		self.message_source_view = MessageSourceView(message.source)
		self.message_source_view.regenerate_clicked.connect(lambda model_source:self.regenerate_clicked.emit(model_source))
		self.left_layout.addWidget(self.message_source_view)
		
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
		self.text_edit = TextEdit()
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
		self.confirm_btn.setFixedWidth(25)
		self.panel_layout.addWidget(self.confirm_btn, alignment=Qt.AlignTop)

		# Expand message view button (rotating arrow)
		self.expand_btn = QToolButton()
		self.expand_btn.setCheckable(True)
		self.expand_btn.setArrowType(Qt.RightArrow)
		self.expand_btn.toggled.connect(self.toggle_expand)
		self.panel_layout.addWidget(self.expand_btn, alignment=Qt.AlignTop)
		
		self.message = message
		QTimer.singleShot(0, self.update_text_edit_height)
	
	def on_should_send_changed(self, state):
		self.message.should_send = state == Qt.Checked
	
	def update_text_edit_height(self):
		self._update_edit_state()
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
	
	def _update_edit_state(self):
		if self.editing:
			self.confirm_btn.setVisible(True)
			self.text_edit.setStyleSheet("QTextEdit {border: 3px solid rgba(0, 0, 255, 0.3);}")
		else:
			self.confirm_btn.setVisible(False)
			self.text_edit.setStyleSheet("QTextEdit {border: 3px solid rgba(0, 0, 0, 0);}")
	
	def on_text_changed(self):
		text = self.text_edit.toPlainText()
		self._update_can_edit()

		if self.edit_enabled and text != self.message.content:
			self.editing = True
		else:
			self.editing = False
		
		self.update_text_edit_height()
		
		# self.token_count_label.setText(f"{tokens_in_string(text)} tokens")
		
	def delete_message(self):
		self.message_deleted_clicked.emit(self)

	def confirm_changes(self):
		if self.editing:
			self.message = self.message.create_edited(self.text_edit.toPlainText())
			self.message_changed.emit(self.message)
	
	def _origional_source(self, source:MessageSource):
		if isinstance(source, EditSource):
			source = EditSource.most_original(source).source
		return source
	
	def _update_can_edit(self):
		#a field added to ModelSource by a model to know if it is done generating, defaults to false for other source types or when loaded from db:
		self.edit_enabled = not getattr(self.message.source, "generating", False) 

	@property
	def message(self):
		return self._message
	@message.setter
	def message(self, value:Message):
		self.editing = False

		if self._message is not None:
			self._message.changed.disconnect(self.on_message_changed)
		self._message = value
		
		if self._message is not None:
			self._message.changed.connect(self.on_message_changed)
		
		self.message_source_view.set_message_source(value.source)
		
		# self.role_label.setText(f"{value.full_role}:")
		# self.token_count_label.setText(f"{tokens_in_message(value)} tokens")
		
		self.text_edit.setPlainText(value.content)
		self._update_can_edit()

		self.date_label.setText(value.creation_time.strftime("%Y-%m-%d %H:%M:%S"))	

		# self.should_send_checkbox.setChecked(value.should_send)
		
		self.background_color = message_color_pallet.get_color(self._origional_source(value.source))
		self.update_text_edit_height()
		self.update()
	
	@run_in_main_thread
	def on_message_changed(self, message: Message):
		# Access the vertical scroll bar
		verticalScrollBar = self.text_edit.verticalScrollBar()
		
		# Calculate the current scroll percentage
		oldMax = verticalScrollBar.maximum()
		oldValue = verticalScrollBar.value()
		wasAtBottom = verticalScrollBar.value() == verticalScrollBar.maximum()
		scrollPercentage = 1 if wasAtBottom else oldValue / oldMax
		
		# Save current selection
		cursor = self.text_edit.textCursor()
		anchorPos = cursor.anchor()
		cursorPos = cursor.position()

		# Set new text
		self.text_edit.setPlainText(message.content)

		# Try to restore selection
		# Restore selection
		cursor = self.text_edit.textCursor()
		cursor.setPosition(anchorPos)
		cursor.setPosition(cursorPos, QTextCursor.KeepAnchor)
		self.text_edit.setTextCursor(cursor)

		# Restore the scroll position
		if wasAtBottom:
			#Auto scroll:
			verticalScrollBar.setValue(verticalScrollBar.maximum())
		else:
			# Calculate the new scroll position based on the old percentage
			newMax = verticalScrollBar.maximum()
			newValue = newMax * (scrollPercentage * oldMax / newMax)
			verticalScrollBar.setValue(int(newValue))

		self.text_edit.setStyleSheet("")
		self.update_text_edit_height()