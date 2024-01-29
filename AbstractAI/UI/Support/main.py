from AbstractAI.UI.Support.MessageView import *
from AbstractAI.UI.Support.ConversationView import *
from AbstractAI.UI.Support.ChatUI import *
from AbstractAI.UI.Support.ConversationListView import *

import json
from ClassyFlaskDB.Flaskify.serialization import FlaskifyJSONEncoder
from ClassyFlaskDB.DATA import DATAEngine

from datetime import datetime
from copy import deepcopy

from PyQt5.QtWidgets import *

class Application(QMainWindow):
	@property
	def conversation(self) -> Conversation:
		return self.chatUI.conversation
	@conversation.setter
	def conversation(self, value:Conversation):
		self.name_field.setText(value.name)
		self.description_field.setText(value.description)
		self.chatUI.conversation = value
		self.conversation_list_view.set_selected(value)
		
	def __init__(self, app: QApplication):
		super().__init__()
		self.app = app
		self.engine = DATAEngine(ConversationDATA, engine_str="sqlite:///chats.db")
		self.conversations = ConversationCollection.all_from_engine(self.engine)
		
		self.init_ui()
		self.conversation = self.new_conversation()
	
	def init_ui(self):
		#split view:
		self.splitter = QSplitter(Qt.Horizontal)
		self.left_panel = QVBoxLayout()
		self.sort_controls = QHBoxLayout()
		self.sort_controls.addWidget(QLabel("Sort By:"))
		self.sort_selector = QComboBox()
		self.sort_selector.addItems(["Created", "Modified", "Name"])
		self.sort_controls.addWidget(self.sort_selector)
		self.left_panel.addLayout(self.sort_controls)
		
		self.search_area = QHBoxLayout()
		self.search_field = QLineEdit()
		self.search_field.setPlaceholderText("Search...")
		self.search_area.addWidget(self.search_field)
		#search button with magnifying glass icon:
		self.search_button = QPushButton()
		self.search_button.setIcon(QIcon.fromTheme("edit-find"))
		self.search_area.addWidget(self.search_button)
		self.left_panel.addLayout(self.search_area)
		
		self.conversation_list_view = ConversationListView(self.conversations)
		def set_conv(conv):
			self.conversation = conv
		self.conversation_list_view.conversation_selected.connect(set_conv)
		self.left_panel.addWidget(self.conversation_list_view)
		
		self.new_conversation_layout = QHBoxLayout()
		self.new_conversation_name = QLineEdit()
		self.new_conversation_name.setPlaceholderText("New Conversation Name...")
		self.new_conversation_layout.addWidget(self.new_conversation_name)
		self.new_conversation_button = QPushButton()
		self.new_conversation_button.setIcon(QIcon.fromTheme("list-add"))
		self.new_conversation_button.clicked.connect(self.new_conversation)
		self.new_conversation_layout.addWidget(self.new_conversation_button)
		self.left_panel.addLayout(self.new_conversation_layout)
		
		w = QWidget()
		w.setLayout(self.left_panel)
		self.splitter.addWidget(w)
		
		self.right_panel = QVBoxLayout()
		self.name_description_layout = QHBoxLayout()
		self.name_field = QLineEdit()
		self.name_field.setPlaceholderText("Conversation Name...")
		self.name_field.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
		self.name_field.setMinimumSize(150, 0)
		self.name_description_layout.addWidget(self.name_field)
		self.description_field = QLineEdit()
		self.description_field.setPlaceholderText("Conversation Description...")
		self.name_description_layout.addWidget(self.description_field)
		self.name_description_confirm_button = QPushButton()
		self.name_description_confirm_button.setIcon(QIcon.fromTheme("emblem-default"))
		self.name_description_confirm_button.clicked.connect(self._name_description_confirm)
		self.name_description_layout.addWidget(self.name_description_confirm_button)
		self.right_panel.addLayout(self.name_description_layout)
		
		self.chatUI = ChatUI()
		self.right_panel.addWidget(self.chatUI)
		
		w = QWidget()
		w.setLayout(self.right_panel)
		self.splitter.addWidget(w)
		
		# Make the left panel keep its size:
		self.splitter.setStretchFactor(0, 0)
		self.splitter.setStretchFactor(1, 1)
		self.setCentralWidget(self.splitter)
	
	def new_conversation(self):
		name = self.new_conversation_name.text()
		if name == "":
			name = "New Conversation"
		conv = Conversation(name, f"A conversation created at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
		self.conversations.append(conv)
		return conv
	
	def _name_description_confirm(self):
		if self.conversation is None:
			return
		
		if self.conversation.name != self.name_field.text() or self.conversation.description != self.description_field.text():
			self.conversation.name = self.name_field.text()
			self.conversation.description = self.description_field.text()
			self.conversation.last_modified = get_local_time()
			self.conversation_list_view.update_conversation(self.conversation)
			self.engine.merge(self.conversation)

if __name__ == "__main__":
	app = QApplication(sys.argv)
	window = Application(app)
	window.show()
	sys.exit(app.exec_())