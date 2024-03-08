from PyQt5.QtWidgets import QListWidget, QListWidgetItem
from AbstractAI.UI.ChatViews.ConversationView import ConversationView, Conversation, ConversationCollection
from AbstractAI.UI.Context import Context
from PyQt5.QtCore import pyqtSignal
from enum import Enum

from typing import List

class SortByType(Enum):
	'''
	An enum class that represents the different ways to sort the conversations.
	'''
	CREATION_TIME = "Created"
	LAST_MODIFIED = "Modified"
	NAME = "Name"

class ConversationListView(QListWidget):
	'''
	Displays a list of conversations and emits a signal when a conversation is selected.
	'''
	@property
	def conversations(self) -> ConversationCollection:
		return self._conversations
	@conversations.setter
	def conversations(self, value:ConversationCollection):
		if getattr(self, "_conversations", None) is not None:
			self._conversations.conversation_added.disconnect(self._redraw_conversation)
			
		self._conversations = value
		self._redraw_items(self._conversations.conversations)
		self._conversations.conversation_added.connect(self._redraw_conversation)
		
		if Context.conversation is not None:
			if Context.conversation.auto_id in self._conversations.conversation_indicies:
				Context.conversation._item.setSelected(True)
				self.scrollToItem(Context.conversation._item)
			
	def __init__(self, conversations: ConversationCollection):
		super().__init__()
		self._redrawing = False
		def conversation_selected():
			if self._redrawing:
				return
			self.set_selected(Context.conversation)
		Context.conversation_selected.connect(conversation_selected)
		self.conversations = conversations
		self.itemSelectionChanged.connect(self.update_selection)
	
	def _redraw_conversation(self, conversation: Conversation, is_selected:bool=None):
		if not conversation.auto_id in self.items_map:
			item = QListWidgetItem(self)
			item.conversation = conversation.auto_id
			self.items_map[conversation.auto_id] = item
			self.addItem(item)
		else:
			item = self.items_map[conversation.auto_id]
			
		item.setText(conversation.name)
		item.setToolTip(f"{conversation.name}\nCreated at {conversation.creation_time.strftime('%Y-%m-%d %H:%M:%S')}\nLast modified at {conversation.last_modified.strftime('%Y-%m-%d %H:%M:%S')}\n\n{conversation.description}")
		if is_selected is not None:
			item.setSelected(is_selected)
		conversation._item = item
		
	def _redraw_items(self, conversations:List[Conversation]):
		self._redrawing = True
		selected_ids = [item.conversation for item in self.selectedItems()]
		self.items_map = {}
		self.clear()
		
		for conversation in conversations:
			self._redraw_conversation(conversation, is_selected=conversation.auto_id in selected_ids)
		self._redrawing = False
		
	def sort_by(self, sort_type:SortByType):
		'''
		Sort the conversations by the given type.
		'''
		sorted_conversations = []
		print("\n".join([str(conversation.creation_time) for conversation in self.conversations]))
		if sort_type == SortByType.CREATION_TIME:
			sorted_conversations = sorted(self.conversations, key=lambda conversation: conversation.creation_time)
		elif sort_type == SortByType.LAST_MODIFIED:
			sorted_conversations = sorted(self.conversations, key=lambda conversation: conversation.last_modified)
		elif sort_type == SortByType.NAME:
			sorted_conversations = sorted(self.conversations, key=lambda conversation: conversation.name)
		
		self._redraw_items(sorted_conversations)
		
	def update_selection(self):
		if self._redrawing:
			return
		
		self._redrawing = True
		for item in self.selectedItems():
			Context.conversation = self.conversations.load_completely(item.conversation)
			break
		self._redrawing = False
	
	def set_selected(self, conversation:Conversation):
		if conversation.auto_id in self.items_map:
			self.setCurrentItem(self.items_map[conversation.auto_id])
		else:
			self.setCurrentItem(None)