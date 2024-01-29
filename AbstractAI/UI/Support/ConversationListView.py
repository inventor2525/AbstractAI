from PyQt5.QtWidgets import QListWidget, QListWidgetItem
from AbstractAI.UI.Support.ConversationView import ConversationView, Conversation, ConversationCollection
from PyQt5.QtCore import pyqtSignal

from typing import List

class ConversationListView(QListWidget):
	'''
	Displays a list of conversations and emits a signal when a conversation is selected.
	'''
	conversation_selected = pyqtSignal(Conversation)
	
	@property
	def conversations(self) -> ConversationCollection:
		return self._conversations
	@conversations.setter
	def conversations(self, value:ConversationCollection):
		if getattr(self, "_conversations", None) is not None:
			self._conversations.conversation_added.disconnect(self.update_conversation)
			
		self._conversations = value
		self.items_map = {}
		self.clear()
		
		for conversation in self._conversations:
			self.update_conversation(conversation)
		self._conversations.conversation_added.connect(self.update_conversation)
			
	def __init__(self, conversations: ConversationCollection):
		super().__init__()
		self.conversations = conversations
		self.itemSelectionChanged.connect(self.update_selection)
	
	def update_conversation(self, conversation: Conversation):
		if not conversation.auto_id in self.items_map:
			item = QListWidgetItem(self)
			self.items_map[conversation.auto_id] = item
			self.addItem(item)
		else:
			item = self.items_map[conversation.auto_id]
			
		item.setText(conversation.name)
		item.setToolTip(f"{conversation.name}\nCreated at {conversation.creation_time.strftime('%Y-%m-%d %H:%M:%S')}\nLast modified at {conversation.last_modified.strftime('%Y-%m-%d %H:%M:%S')}\n\n{conversation.description}")
		
	def update_selection(self):
		for index in range(self.count()):
			item = self.item(index)
			if item.isSelected():
				self.conversation_selected.emit(self.conversations[index])
				break
	
	def set_selected(self, conversation:Conversation):
		if conversation.auto_id in self.items_map:
			self.setCurrentItem(self.items_map[conversation.auto_id])
		else:
			self.setCurrentItem(None)