from AbstractAI.ConversationModel import *
from AbstractAI.Helpers.run_in_main_thread import run_in_main_thread
from .MessageView import *
from PyQt5.QtGui import QWheelEvent

class ConversationView(QListWidget):
	message_changed = pyqtSignal(Message)
	
	regenerate_message = pyqtSignal(ModelSource)
	
	@property
	def conversation(self) -> Conversation:
		return self._conversation
	@conversation.setter
	def conversation(self, value:Conversation):		
		if getattr(self, "_conversation", None) is not None:
			self._conversation.conversation_changed.disconnect(self.render_messages)
			for message in self._conversation.message_sequence.messages:
				del message._view
				del message._item
		self.clear()
		
		self._conversation = value
		if self._conversation is not None:
			self._conversation.conversation_changed.connect(self.render_messages)
			
			for message in self._conversation.message_sequence.messages:
				self.addItem(self._render_message(message))
				self.setItemWidget(message._item, message._view)
			self.scrollToBottom()
	
	def __init__(self, conversation: Conversation = None):
		super().__init__()
		
		self.setAutoScroll(False)
		self.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
		self.setSelectionMode(QAbstractItemView.ExtendedSelection)
		self.itemSelectionChanged.connect(self.update_selection)
		
		self.conversation = conversation
	
	def update_selection(self):
		for index in range(self.count()):
			item = self.item(index)
			message_view = self.itemWidget(item)
			if message_view is not None:
				message_view.set_selected(item.isSelected())

	def wheelEvent(self, event):
		self.verticalScrollBar().setValue(self.verticalScrollBar().value() - event.pixelDelta().y())
	
	def keyPressEvent(self, event):
		item_widget = self.itemWidget(self.currentItem())
		if event.key() == Qt.Key_Delete and not item_widget.text_edit.hasFocus():
			selected_messages = [item.message for item in self.selectedItems()]
			self.conversation.remove_messages(selected_messages)
		elif event.key() == Qt.Key_Escape:
			self.clearSelection()
		else:
			super().keyPressEvent(event)
	
	def _render_message(self, message: Message) -> QListWidgetItem:
		message_item = QListWidgetItem()
		message_item.message = message
		
		# Create the message view
		message_view = MessageView(message, self)
		message_view.rowHeightChanged.connect(lambda: self.update_row_height(message_item))
		message_view.regenerate_clicked.connect(lambda msg_source: self.regenerate_message.emit(msg_source))
		def message_changed(message: Message):
			self.conversation.replace_message(message.source.original, message.source.new, True)
			self.message_changed.emit(message)
			self.update_row_height(message_item)
		message_view.message_changed.connect(message_changed)
		
		# Set the message view as the widget for the item
		message_item.setSizeHint(message_view.sizeHint())
		message._view = message_view
		message._item = message_item
		return message_item
	
	def _remove_row(self, row: int) -> None:
		item = self.item(row)
		message = item.message
		self.takeItem(row)
		del message._view
		del message._item
		
	@run_in_main_thread
	def render_messages(self, *args):
		if self.conversation is None or self.conversation.message_sequence is None or len(self.conversation.message_sequence) == 0:
			self.clear()
			return
		
		def insert(msg_index, msg):
			self.insertItem(msg_index, self._render_message(msg))
			self.setItemWidget(msg._item, msg._view)
			
		for msg_index, msg in enumerate(self.conversation.message_sequence.messages):
			msg_item = getattr(msg, "_item", None)
			
			if msg_item is None:
				insert(msg_index, msg)
			else:
				while self.item(msg_index) != msg_item and msg_index < self.count():
					self._remove_row(msg_index)
				if msg_index >= self.count():
					insert(msg_index, msg)
		for i in range(msg_index+1, self.count()):
			self.takeItem(i)
		
	def update_row_height(self, item: QListWidgetItem):
		try:
			item_widget = self.itemWidget(item)
			item.setSizeHint(QSize(0, item_widget.sizeHint().height()))
		except:
			pass