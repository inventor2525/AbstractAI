from AbstractAI.Conversation import *
from .MessageView import *

class ConversationView(QListWidget):
	message_changed = pyqtSignal(Message, str) # Message, old hash
	
	def __init__(self, conversation: Conversation, *args, **kwargs):
		super().__init__(*args, **kwargs)
		
		self.colors = QColor.colorNames()#  ['red', 'green', 'blue', 'yellow', 'cyan', 'magenta', 'gray']
		
		self._color_palette = {
			"system": "lightgrey",
			"user human": "#9DFFA6",
			"user terminal": "#FFEBE4",
			"assistant": "#FFC4B0",
		}
		
		self.conversation = conversation
		
		for message in conversation.messages:
			self.render_message(message)
			
		self.setAutoScroll(False)
		self.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
		self.setSelectionMode(QAbstractItemView.ExtendedSelection)
		self.itemSelectionChanged.connect(self.update_selection)
	
	@property
	def color_palette(self):
		if not hasattr(self, '_color_palette') or self._color_palette is None:
			self._color_palette = {}
			message_types = set()

			# Extract message types from the messages in the conversation
			for message in self.conversation.messages:
				message_types.add(message.full_role.lower())

			# Assign colors to message types
			for i, message_type in enumerate(sorted(message_types)):
				message_type = message_type.lower()
				self._color_palette[message_type] = self.colors[i % len(self.colors)]

		return self._color_palette
		
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
				self.conversation.messages.remove(message_to_remove)
				
				self.clearSelection()
	
	def render_message(self, message: Message):
		message_type = message.full_role.lower()
		if message_type not in self.color_palette:
			self._color_palette[message_type] = self.colors[len(self._color_palette) % len(self.colors)]
			
		item = QListWidgetItem()
		item_widget = MessageView(message, self)
		item_widget.rowHeightChanged.connect(lambda: self.update_row_height(item))
		def message_changed(message: Message, old_hash: str):
			self.message_changed.emit(message, old_hash)
			self.conversation.recompute_hash()
			self.update_row_height(item)
		item_widget.message_changed.connect(message_changed)
		item.setSizeHint(item_widget.sizeHint())
		self.addItem(item)
		self.setItemWidget(item, item_widget)
		self.scrollToBottom()
				
	def add_message(self, message: Message):
		self.conversation.add_message(message)
		self.render_message(message)
		
	def update_row_height(self, item: QListWidgetItem):
		item_widget = self.itemWidget(item)
		item.setSizeHint(QSize(item_widget.sizeHint().width(), item_widget.sizeHint().height()))
