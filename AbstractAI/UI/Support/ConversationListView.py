from PyQt5.QtWidgets import QListWidget, QListWidgetItem
from AbstractAI.UI.Support.ConversationView import ConversationView, Conversation, ConversationCollection
from PyQt5.QtCore import pyqtSignal

from typing import List

class ConversationListView(QListWidget):
	'''
	Displays a list of conversations and emits a signal when a conversation is selected.
	'''
	conversation_selected = pyqtSignal(Conversation)
	
	def __init__(self, conversations: ConversationCollection):
		super().__init__()
		self.conversations = conversations
		for conversation in conversations:
			self._add_conversation(conversation)
		self.conversations.conversation_added.connect(self._add_conversation)
		
		self.itemSelectionChanged.connect(self.update_selection)
	
	def _add_conversation(self, conversation: Conversation):
		item = QListWidgetItem(self)
		item.setText(conversation.name)
		item.setToolTip(f"{conversation.name}\nCreated at {conversation.creation_time.strftime('%Y-%m-%d %H:%M:%S')}\nLast modified at {conversation.last_modified.strftime('%Y-%m-%d %H:%M:%S')}\n\n{conversation.description}")
		self.addItem(item)
	
	def update_selection(self):
		for index in range(self.count()):
			item = self.item(index)
			if item.isSelected():
				self.conversation_selected.emit(self.conversations[index])
				break