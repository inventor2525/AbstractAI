from PyQt5.QtWidgets import QListWidget, QListWidgetItem
from AbstractAI.UI.Support.ConversationView import ConversationView, Conversation
from PyQt5.QtCore import pyqtSignal

from typing import List

class ConversationListView(QListWidget):
	'''
	Displays a list of conversations and emits a signal when a conversation is selected.
	'''
	conversation_selected = pyqtSignal(Conversation)
	
	def __init__(self, conversations: List[Conversation]):
		super().__init__()
		self.conversations = []
		for conversation in conversations:
			self.add_conversation(conversation)
		self.itemSelectionChanged.connect(self.update_selection)
	
	def add_conversation(self, conversation):
		self.conversations.append(conversation)
		item = QListWidgetItem(self)
		item.setText(conversation.name)
		item.setToolTip(f"{conversation.name}\nCreated at {conversation.creation_time.strftime('%Y-%m-%d %H:%M:%S')}")
		self.addItem(item)
	
	def update_selection(self):
		for index in range(self.count()):
			item = self.item(index)
			if item.isSelected():
				self.conversation_selected.emit(self.conversations[index])
				break