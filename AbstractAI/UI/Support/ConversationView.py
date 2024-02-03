from AbstractAI.ConversationModel import *
from AbstractAI.Helpers.run_in_main_thread import run_in_main_thread
from .MessageView import *

class ConversationView(QListWidget):
	message_changed = pyqtSignal(Message) # Message
	
	@property
	def conversation(self) -> Conversation:
		return self._conversation
	@conversation.setter
	def conversation(self, value:Conversation):
		if getattr(self, "_conversation", None) is not None:
			self._conversation.message_added.disconnect(self.render_message)
		self.clear()
		
		self._conversation = value
		if self._conversation is not None:
			self._conversation.message_added.connect(self.render_message)
			
			for message in self._conversation.message_sequence.messages:
				self._render_message(message)
	
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
	
	def keyPressEvent(self, event):
		item_widget = self.itemWidget(self.currentItem())
		if event.key() == Qt.Key_Delete and not item_widget.text_edit.hasFocus():
			#if selection is not empty, delete all selected messages
			if self.selectedItems():
				for item in self.selectedItems():
					item_widget = self.itemWidget(item)
					self.delete_message(item_widget)
		elif event.key() == Qt.Key_Escape:
			self.clearSelection()
		else:
			super().keyPressEvent(event)
	
	def delete_message(self, message_widget): #TODO: this needs to take a message not a widget
		if message_widget is not None:
			item = None
			for index in range(self.count()):
				current_item = self.item(index)
				if self.itemWidget(current_item) == message_widget:
					item = current_item
					break

			if item is not None:
				row = self.row(item)
				item = self.takeItem(row)

				message_to_remove = message_widget.message
				self.conversation.remove_message(message_to_remove)
				
				self.clearSelection()
	
	def _render_message(self, message: Message):
		item = QListWidgetItem()
		item_widget = MessageView(message, self)
		item_widget.rowHeightChanged.connect(lambda: self.update_row_height(item))
		def message_changed(message: Message):
			self.conversation.replace_message(message.source.original, message.source.new, True)
			self.message_changed.emit(message)
			self.update_row_height(item)
		item_widget.message_changed.connect(message_changed)
		item.setSizeHint(item_widget.sizeHint())
		self.addItem(item)
		self.setItemWidget(item, item_widget)
		item_widget.message_deleted_clicked.connect(self.delete_message)
		self.scrollToBottom()
	
	@run_in_main_thread
	def render_message(self, message: Message):
		self._render_message(message)
		
	def update_row_height(self, item: QListWidgetItem):
		item_widget = self.itemWidget(item)
		item.setSizeHint(QSize(item_widget.sizeHint().width(), item_widget.sizeHint().height()))
	