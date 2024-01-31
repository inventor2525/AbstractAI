from AbstractAI.UI.Support.MessageView import *
from AbstractAI.UI.Support.ConversationView import *
from AbstractAI.UI.Support.ChatUI import *
from AbstractAI.UI.Support.ConversationListView import *
from AbstractAI.LLMs.ModelLoader import ModelLoader, LLM

import json
from ClassyFlaskDB.Flaskify.serialization import FlaskifyJSONEncoder
from ClassyFlaskDB.DATA import DATAEngine

from datetime import datetime
from copy import deepcopy

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

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
		
	def __init__(self, model_loader:ModelLoader):
		super().__init__()
		self.model_loader = model_loader
		
		self.app = QApplication.instance()
		self.engine = DATAEngine(ConversationDATA, engine_str="sqlite:///chats.db")
		self.conversations = ConversationCollection.all_from_engine(self.engine)
		
		self.should_filter = False
		self.filter_timmer = QTimer()
		self.filter_timmer.setInterval(500)
		def filter_timmer_timeout():
			if self.should_filter:
				self.search_name_description()
				self.should_filter = False
		self.filter_timmer.timeout.connect(filter_timmer_timeout)
		self.filter_timmer.start()
		
		self.init_ui()
		self.conversation = self.new_conversation()
		
		self.read_settings()
		
		self.llm : LLM = None
	
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
		self.search_field.textChanged.connect(lambda: setattr(self, "should_filter", True))
		self.search_area.addWidget(self.search_field)
		#search button with magnifying glass icon:
		self.search_button = QPushButton()
		self.search_button.setIcon(QIcon.fromTheme("edit-find"))
		self.search_button.clicked.connect(self.search_contents)
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
		self.models_combobox = QComboBox()
		self.models_combobox.addItem("Select A Model...")
		self.models_combobox.addItems(self.model_loader.model_names)
		self.models_combobox.currentTextChanged.connect(self.select_model)
		self.name_description_layout.addWidget(self.models_combobox)
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
		self.chatUI.message_sent.connect(self.user_sent_message)
		
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
	
	def search_name_description(self):
		search = self.search_field.text()
		if search == "":
			self.conversation_list_view.conversations = self.conversations
		else:
			self.conversation_list_view.conversations = ConversationCollection([conv for conv in self.conversations if search.lower() in conv.name.lower() or search.lower() in conv.description.lower()])
	
	def search_contents(self):
		'''
		Searches the contents of all messages in all conversations and
		filters the conversation list to only show conversations that
		contain the search text.
		'''
		search = self.search_field.text()
		if search == "":
			self.conversation_list_view.conversations = self.conversations
		else:
			filtered_conversations = []
			for conversation in self.conversations:
				for message in conversation.message_sequence:
					if search.lower() in message.content.lower():
						filtered_conversations.append(conversation)
			self.conversation_list_view.conversations = ConversationCollection(filtered_conversations)
	
	def read_settings(self):
		settings = QSettings("MyCompany", "MyApp")
		self.restoreGeometry(settings.value("geometry", QByteArray()))

	def write_settings(self):
		settings = QSettings("MyCompany", "MyApp") #TODO: Move settings to the main window to be and add which conv was open as well as what more (columns, tabs, or windows) the ui is in
		settings.setValue("geometry", self.saveGeometry())
	
	def closeEvent(self, event):
		self.write_settings()
		super().closeEvent(event)
	
	def user_sent_message(self, conversation:Conversation, new_message:Message):
		if self.llm is None:
			#Show error an message using a QMessageBox
			QMessageBox.critical(self, "No LLM Loaded", "Please load an LLM before sending messages.")
			return
		
		response = self.llm.chat(conversation)
		conversation.add_message(response.message)
	
	def select_model(self, model_name:str):
		if self.models_combobox.itemText(0) == "Select A Model...":
			self.models_combobox.removeItem(0)
			
		self.llm = self.model_loader[model_name]
		self.llm.start()
		
if __name__ == "__main__":
	app = QApplication(sys.argv)
	models = {
		"Mixtral": {
			"LoaderType": "LLamaCPP",
			"ModelName": "Mixtral",
			"ModelPath": "/home/charlie/Projects/text-generation-webui/models/mixtral-8x7b-instruct-v0.1.Q4_K_M.gguf",
			"Parameters": {}
		}
	}
	model_loader = ModelLoader(models)
	window = Application(model_loader)
	window.show()
	sys.exit(app.exec_())