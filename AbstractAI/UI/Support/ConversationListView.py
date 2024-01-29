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
		self.items_map = {}
		
		for conversation in conversations:
			self.update_conversation(conversation)
		self.conversations.conversation_added.connect(self.update_conversation)

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