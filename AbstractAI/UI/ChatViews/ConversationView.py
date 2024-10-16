from AbstractAI.Model.Converse import *
from AbstractAI.Helpers.run_in_main_thread import run_in_main_thread
from .MessageView import *
from PyQt5.QtGui import QWheelEvent
from typing import Iterator
class ConversationView(QListWidget):
	message_changed = pyqtSignal(Message)
	selection_changed = pyqtSignal()
	
	regenerate_message = pyqtSignal(ModelSource)
	
	@property
	def conversation(self) -> Conversation:
		return self._conversation
	@conversation.setter
	def conversation(self, value:Conversation):		
		if getattr(self, "_conversation", None) is not None:
			self._conversation.conversation_changed.disconnect(self.render_messages)
			for message in self._conversation.message_sequence.messages:
				try:
					del message._view
					del message._item
				except Exception as e:
					pass
		self.clear()
		
		self._conversation = value
		if self._conversation is not None:
			self._conversation.conversation_changed.connect(self.render_messages)
			
			for message in self._conversation.message_sequence.messages:
				self.addItem(self._render_message(message))
				self.setItemWidget(message._item, message._view)
			self.scrollToBottom()
	
	@property
	def currentMessage(self) -> Message:
		if self.currentItem() is not None:
			return self.currentItem().message
		return None
	
	def __init__(self, conversation: Conversation = None):
		super().__init__()
		
		self.setAutoScroll(True)
		self._auto_scroll = True
		self.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
		self.setSelectionMode(QAbstractItemView.ExtendedSelection)
		self.itemSelectionChanged.connect(self.update_selection)
		self.currentItemChanged.connect(self.update_selection)
		
		self.conversation = conversation
		self.selected_messages:List[int] = []
	
	def update_selection(self):
		self.selected_messages = []
		for index in range(self.count()):
			item = self.item(index)
			message_view = self.itemWidget(item)
			if message_view is not None:
				if item.isSelected():
					self.selected_messages.append(index)
				message_view.set_selected(item.isSelected())
				if item is not self.currentItem():
					message_view.text_edit.clearFocus()
					message_view.text_edit.clearSelection()
		if len(self.selectedItems()) > 1:
			self.setFocus()
		self.selection_changed.emit()
	
	def clearSelection(self) -> None:
		item = self.currentItem()
		if item is not None:
			message_view = self.itemWidget(item)
			message_view.text_edit.clearFocus()
			message_view.text_edit.clearSelection()
			
		self.selected_messages = []
		self.selection_changed.emit()
		return super().clearSelection()
	
	def wheelEvent(self, event):
		self.verticalScrollBar().setValue(self.verticalScrollBar().value() - event.pixelDelta().y())
		self._auto_scroll = self.verticalScrollBar().value() == self.verticalScrollBar().maximum()
	
	def keyPressEvent(self, event):
		item_widget = self.itemWidget(self.currentItem())
		if item_widget is None:
			super().keyPressEvent(event)
			return
		
		if event.key() == Qt.Key_Escape:
			self.clearSelection()
		elif not item_widget.text_edit.hasFocus():
			if event.key() == Qt.Key_Delete:
				selected_messages = [item.message for item in self.selectedItems()]
				self.conversation.remove_messages(selected_messages)
			elif event.key() == Qt.Key_Left:
				if self.currentItem() is not None:
					message = self.currentItem().message
					if message._view.left_arrow_btn.isVisible():
						self._auto_scroll = False
						message._view.left_arrow_btn.click()
			elif event.key() == Qt.Key_Right:
				if self.currentItem() is not None:
					message = self.currentItem().message
					if message._view.right_arrow_btn.isVisible():
						self._auto_scroll = False
						message._view.right_arrow_btn.click()
			
			elif event.modifiers() & Qt.KeyboardModifier.ControlModifier and event.key() == Qt.Key_C:
				selected_message_ids = set([id(item.message) for item in self.selectedItems()])
				self.clipboard = [message for message in self.conversation if id(message) in selected_message_ids]
			elif event.modifiers() & Qt.KeyboardModifier.ControlModifier and event.key() == Qt.Key_V:
				clipboard = getattr(self, "clipboard", [])
				copied = Conversation.copy_messages(clipboard)
				current_item = self.currentItem()
				if event.modifiers() & Qt.KeyboardModifier.ShiftModifier and current_item:
					insert_index = self.conversation.message_sequence.messages.index(current_item.message)
					self.conversation.insert_messages(copied, insert_index)
				else:
					self.conversation.add_messages(copied)
			else:
				super().keyPressEvent(event)
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
			edit = message.get_source(EditSource)
			if edit:
				self.conversation.replace_message(edit.original, edit.new, True)
				self.message_changed.emit(message)
				self.update_row_height(message_item)
		message_view.message_changed.connect(message_changed)
		
		# Set the message view as the widget for the item
		message_item.setSizeHint(message_view.sizeHint())
		message._view = message_view
		message._item = message_item
		
		def message_selected(msg:Message):
			if getattr(msg, "_view", None) is None:
				try:
					message_view.message_selected.disconnect()
				except:
					pass
				return
			has_focus = msg._view.text_edit.hasFocus()
			scroll_val = self.verticalScrollBar().value()
			if msg.auto_id == getattr(self.currentMessage, "auto_id", None):
				if len(self.selectedItems()) > 1:
					self.clearSelection()
			else:
				self.clearSelection()
			self.setCurrentItem(msg._item)
			if has_focus:
				msg._view.text_edit.setFocus()
			self.verticalScrollBar().setValue(scroll_val)
		
		message_view.message_selected.connect(message_selected)
		return message_item
	
	def _remove_row(self, row: int) -> None:
		item = self.item(row)
		message = item.message
		self.takeItem(row)
		message._view.message_selected.disconnect()
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
				while self.item(msg_index) != msg_item:
					try:
						self._remove_row(msg_index)
					except:
						insert(msg_index, msg)
						break
	
		remove_index = msg_index+1
		for i in range(remove_index, self.count()):
			m = self.item(remove_index).message
			del m._view
			del m._item
			self.takeItem(remove_index)
		
	def update_row_height(self, item: QListWidgetItem):
		try:
			item_widget = self.itemWidget(item)
			item.setSizeHint(QSize(0, item_widget.sizeHint().height()))
			if self._auto_scroll:
				self.verticalScrollBar().setValue(self.verticalScrollBar().maximum())
		except:
			pass