from AbstractAI.UI.Support.ColoredFrame import *
from AbstractAI.UI.Elements.TextEdit import TextEdit
from AbstractAI.UI.Elements.FlashingButton import FlashingButton
from AbstractAI.Model.Converse import Message, MessageSequence
from AbstractAI.Model.Converse.MessageSources import *
from AbstractAI.Helpers.run_in_main_thread import run_in_main_thread
from .MessageView_extras.MessageSourceView import MessageSourceView
from AbstractAI.UI.Elements.FileSelector import FileSelectionWidget
from AbstractAI.Model.Converse.Role import *
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QTextCursor
from AbstractAI.AppContext import AppContext
from datetime import datetime
from copy import deepcopy

class BaseMessageView(ColoredFrame):
	def __init__(self, parent, message: Message):
		super().__init__(parent)
		self._message = message
		
class MessageView(BaseMessageView):
	rowHeightChanged = pyqtSignal()
	
	# Signal fired when a message change is confirmed by the user, passes the new message
	message_changed = pyqtSignal(Message)
	
	regenerate_clicked = pyqtSignal(ModelSource)
	
	message_selected = pyqtSignal(Message)
	
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
		
		self.init_ui()
		self.expand_btn.setChecked(getattr(getattr(message, "source", None), "generating", False))
		
		# Set the message to the one passed in
		self.message = message
		QTimer.singleShot(0, self.update_text_edit_height)
	
	def init_ui(self):
		self.layout = QHBoxLayout()
		self.setLayout(self.layout)
		
		self.left_layout = QVBoxLayout()
		self.layout.addLayout(self.left_layout)
		
		# Date label (left side of message)
		self.date_label = QLabel()
		self.date_label.setFixedWidth(100)
		self.date_label.setWordWrap(True)
		self.left_layout.addWidget(self.date_label)
		
		# Message source view (left side of message)
		self.message_source_view = MessageSourceView()
		self.left_layout.addWidget(self.message_source_view)
		
		# Spacer (left side of message)
		self.left_layout.addStretch()
		
		# Horizontal layout for left and right arrow buttons (left side of message)
		self.arrow_layout = QHBoxLayout()
		self.left_layout.addLayout(self.arrow_layout)
		
		def swap_message_sequence():
			self_index = self.message.conversation.message_sequence.messages.index(self.message)
			self.message.conversation.message_sequence = self.alternates[self.alternate_index]
			self._update_arrow_buttons()
			
			self.message.conversation.conversation_changed()
			
			if self_index is not None and self_index < len(self.message.conversation.message_sequence.messages):
				new_self = self.message.conversation.message_sequence.messages[self_index]
				if new_self is not None:
					self.message_selected.emit(new_self)
		# Left arrow button for selecting previous version of message:
		self.left_arrow_btn = QToolButton()
		self.left_arrow_btn.setArrowType(Qt.LeftArrow)
		self.left_arrow_btn.setFixedHeight(15)
		self.left_arrow_btn.setFixedWidth(15)
		def left_arrow_clicked():
			self.alternate_index -= 1
			swap_message_sequence()
		self.left_arrow_btn.clicked.connect(left_arrow_clicked)
		self.arrow_layout.addWidget(self.left_arrow_btn, alignment=Qt.AlignLeft)
		
		# Right arrow button for selecting next version of message:
		self.right_arrow_btn = QToolButton()
		self.right_arrow_btn.setArrowType(Qt.RightArrow)
		self.right_arrow_btn.setFixedHeight(15)
		self.right_arrow_btn.setFixedWidth(15)
		def right_arrow_clicked():
			self.alternate_index += 1
			swap_message_sequence()
		self.right_arrow_btn.clicked.connect(right_arrow_clicked)
		self.arrow_layout.addWidget(self.right_arrow_btn, alignment=Qt.AlignRight)
		
		# Editable text box (The message -- in the middle of the view)
		self.text_edit = TextEdit("Message Text Box")
		self.text_edit.setLineWrapMode(QTextEdit.WidgetWidth)
		self.text_edit.setWordWrapMode(QTextOption.WrapAtWordBoundaryOrAnywhere)
		self.text_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
		self.text_edit.textChanged.connect(self.on_text_changed)
		self.text_edit.textChanged.connect(self.update_text_edit_height)
		self.text_edit.selectionChanged.connect(lambda:self.message_selected.emit(self._message))
		self.layout.addWidget(self.text_edit)
		
		# File selector (A replacement to the message text box when the message is a group of files)
		self.file_selector = FileSelectionWidget()
		self.layout.addWidget(self.file_selector)
		
		# Vertical panel (right side of message)
		self.panel_layout = QVBoxLayout()
		self.panel_layout.setAlignment(Qt.AlignTop)
		self.layout.addLayout(self.panel_layout)

		# Delete button (X -- top right of message)
		self.delete_btn = QPushButton("X")
		self.delete_btn.clicked.connect(self.delete_message)
		self.delete_btn.setFixedWidth(25)
		self.panel_layout.addWidget(self.delete_btn, alignment=Qt.AlignTop)
		
		# Confirm button (checkmark -- top right of message)
		self.confirm_btn = QPushButton("✓")
		self.confirm_btn.clicked.connect(self.confirm_changes)
		self.confirm_btn.setFixedWidth(25)
		self.panel_layout.addWidget(self.confirm_btn, alignment=Qt.AlignTop)
		
		# Confirm button (checkmark -- top right of message)
		self.reload_btn = FlashingButton(QIcon.fromTheme("view-refresh"), "", min_color=QColor.fromRgb(190,0,0), max_color=QColor.fromRgb(255,50,50), interval=.3)
		self.reload_btn.clicked.connect(self.reload_files_message)
		self.reload_btn.setFixedWidth(25)
		self.panel_layout.addWidget(self.reload_btn, alignment=Qt.AlignTop)
		def file_selection_changed():
			self.reload_btn.flashing = True
		self.file_selector.file_selection_changed.connect(file_selection_changed)
			
		# Expand message view button (rotating arrow -- top right of message)
		self.expand_btn = QToolButton()
		self.expand_btn.setCheckable(True)
		self.expand_btn.setArrowType(Qt.RightArrow)
		self.expand_btn.toggled.connect(self.toggle_expand)
		self.panel_layout.addWidget(self.expand_btn, alignment=Qt.AlignTop)
		
		# Add some space on the right side of the message
		self.panel_layout.addStretch()
		
		# Create a button for regenerating the message, if it's from a model (bottom right of message)
		self.regenerate_button = QPushButton(QIcon.fromTheme("view-refresh"), "")
		self.regenerate_button.setMaximumWidth(self.regenerate_button.sizeHint().height())
		self.regenerate_button.clicked.connect(lambda: self.regenerate_clicked.emit(self.message.source))
		self.regenerate_button.setVisible(False)
		self.panel_layout.addWidget(self.regenerate_button)
		
		# Regester the context changed event
		def context_changed():
			self.regenerate_button.setEnabled(AppContext.has_llm(self.message.conversation))
		AppContext.context_changed.connect(context_changed, auto_disconnect=True)
		context_changed()
	
	def _compute_alternates(self):
		self_index = self.message.conversation.message_sequence.index(self.message)
		if self_index == 0 or self_index is None:
			prior_message_in_sequence = None
		else:
			prior_message_in_sequence = self.message.conversation.message_sequence[self_index-1]
		self.alternates = self.message.conversation.alternates(prior_message_in_sequence)
		self.alternates = MessageSequence.filter_sequences_for_next(self.alternates, self_index, keep=self.message.conversation.message_sequence)
		def sort_func(seq):
			messages = getattr(seq,'messages',None)
			si = self_index
			if self_index is None:
				si = 0
			if messages is not None and len(messages) > si:
				return messages[si].date_created
			else:
				m = None
			return getattr(m, 'date_created', datetime.now())
		self.alternates = sorted(self.alternates, key=sort_func, reverse=False)
		#TODO: add ability to browse the end (where a deleted message was)
		#TODO: (optional) speed up alternates calculation by caching results if needed.
		self.alternate_index = self.message.conversation.message_sequence.index_in(self.alternates)
		if self.alternate_index is None:
			raise Exception("Message not found in conversation it is supposed to be in")
		self._update_arrow_buttons()
	
	def _update_arrow_buttons(self):
		self.left_arrow_btn.setVisible(self.alternate_index > 0)
		self.right_arrow_btn.setVisible(self.alternate_index < len(self.alternates)-1)
	
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
			set_height(max(new_height, self.text_edit.doc_height()))
		else:
			set_height(new_height)
		
		self.expand_btn.setVisible(self.text_edit.doc_height() > new_height)
		self.rowHeightChanged.emit()
	
	def resizeEvent(self, event):
		self.update_text_edit_height()
		super().resizeEvent(event)
	
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
		
	def delete_message(self):
		self.message.conversation.remove_message(self.message)

	def confirm_changes(self):
		if self.editing:
			self.message = self.message.create_edited(self.text_edit.toPlainText(), AppContext.user_source)
			self.message_changed.emit(self.message)
	
	def reload_files_message(self):
		files_source = self.message.get_source(FilesSource, expand_edits=True)
		if not files_source:
			return
		
		new_source = FilesSource.from_items(deepcopy(self.file_selector.items)) | AppContext.user_source
		new_content = new_source.load()
		self.message = self.message.create_edited(new_content, source_of_edit=new_source)
		self.message_changed.emit(self.message)
	
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
			self._message.changed.connect(self.on_message_changed, auto_disconnect=True)
		
		self.message_source_view.message_source = value.source
		
		files_source = value.get_source(FilesSource, expand_edits=True)
		
		if files_source:
			self.text_edit.setVisible(False)
			self.file_selector.setVisible(True)
			self.file_selector.items = deepcopy(files_source.items.items)
			self.file_selector.refresh()
		else:
			self.text_edit.setVisible(True)
			self.file_selector.setVisible(False)
			self.text_edit.setPlainText(value.content)
		self._update_can_edit()

		self.date_label.setText(value.date_created.strftime("%Y-%m-%d %H:%M:%S"))
	
		if files_source:
			self.background_color = QColor("#7DDF86")
		else:
			if value.role.type == Role.User().type:
				self.background_color = QColor("#9DFFA6")
			elif value.role.type == Role.Assistant().type:
				self.background_color = QColor("#FFC4B0")
			elif value.role.type == Role.System().type:
				self.background_color = QColor("lightgrey")
			else:
				self.background_color = QColor(Qt.white)
		
		model_source = value.get_source(ModelSource, expand_edits=True)
		self.regenerate_button.setVisible(model_source is not None)
		self.reload_btn.setVisible(files_source is not None)
		
		self._compute_alternates()
		self.update_text_edit_height()
		self.update()
	
	@run_in_main_thread
	def on_message_changed(self, message: Message):
		try:
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

			self.update_text_edit_height()
		except Exception as e:
			pass