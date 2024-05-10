from AbstractAI.Helpers.Stopwatch import Stopwatch
Stopwatch.singleton = Stopwatch(True)
Stopwatch = Stopwatch.singleton

Stopwatch("Startup", log_statistics=False)
Stopwatch.new_scope()
Stopwatch("Imports", log_statistics=False)
Stopwatch.new_scope()

Stopwatch("UI", log_statistics=False)
from AbstractAI.UI.ChatViews.MessageView_extras import *
from AbstractAI.UI.ChatViews.ConversationView import *
from AbstractAI.UI.ChatViews.ChatUI import *
from AbstractAI.UI.ChatViews.ConversationListView import *
from AbstractAI.UI.Support.BackgroundTask import BackgroundTask
from AbstractAI.UI.Support.APIKeyGetter import APIKeyGetter
from AbstractAI.UI.Context import Context
from AbstractAI.UI.Windows.Settings import SettingsWindow, SettingItem

Stopwatch("Remote client", log_statistics=False)
from AbstractAI.Remote.client import System, RemoteLLM
Stopwatch("ModelLoader", log_statistics=False)
from AbstractAI.LLMs.ModelLoader import ModelLoader, LLM

Stopwatch("DATAEngine", log_statistics=False)
from ClassyFlaskDB.DATA import DATAEngine

Stopwatch("basics", log_statistics=False)
import json
from datetime import datetime
from copy import deepcopy
from AbstractAI.Helpers.JSONEncoder import JSONEncoder
import argparse
import os

Stopwatch("PyQT5", log_statistics=False)
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

Stopwatch("Application", log_statistics=False)
class Application(QMainWindow):	
	@property
	def llm(self) -> LLM:
		return self._llm
	@llm.setter
	def llm(self, value:LLM):
		self._llm = value
		Context.llm_loaded = value is not None
		Context.context_changed()
		
	def __init__(self):
		super().__init__()
		Stopwatch.new_scope()
		self.setWindowTitle("AbstractAI")
		self.app = QApplication.instance()
		Stopwatch("Connect to database", log_statistics=False)
		
		self.settings_window = SettingsWindow()
		self.engine = DATAEngine(ConversationDATA, engine_str=f"sqlite:///{Context.args.storage_location}")
		
		Stopwatch("Load conversations", log_statistics=False)
		self.conversations = ConversationCollection.all_from_engine(self.engine)
		
		Stopwatch("Setup UI", log_statistics=False)
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
		def conversation_selected(prev_conversation:Conversation, new_conversation:Conversation):
			self.name_field.setText(new_conversation.name)
			self.description_field.setText(new_conversation.description)
			self.chatUI.conversation = new_conversation
		Context.conversation_selected.connect(conversation_selected)
		Context.conversation = self.new_conversation()
		Context.context_changed()
		
		self.read_settings()
		
		self.llm : LLM = None
		
		Stopwatch.end_scope(log_statistics=False)
	
	def init_ui(self):
		#split view:
		self.splitter = QSplitter(Qt.Horizontal)
		self.left_panel = QVBoxLayout()
		self.sort_controls = QHBoxLayout()
		self.sort_controls.addWidget(QLabel("Sort By:"))
		self.sort_selector = QComboBox()
		self.sort_selector.addItems([
			SortByType.CREATION_TIME.value,
			SortByType.LAST_MODIFIED.value, 
			SortByType.NAME.value
		])
		self.sort_selector.currentTextChanged.connect(lambda: self.conversation_list_view.sort_by(SortByType(self.sort_selector.currentText())))
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
		self.left_panel.addWidget(self.conversation_list_view)
		
		self.bottom_left_layout = QHBoxLayout()
		
		self.settings_button = QToolButton()
		self.settings_button.setText("Settings")
		self.settings_button.setCheckable(True)
		self.settings_button.clicked.connect(self.toggle_settings_window)
		self.bottom_left_layout.addWidget(self.settings_button)
		self.settings_button.setStyleSheet("QToolButton { padding: 2px; }")
		self.settings_window.closed.connect(lambda: self.settings_button.setChecked(False))
		
		self.new_conversation_name = QLineEdit()
		self.new_conversation_name.setPlaceholderText("New Conversation Name...")
		self.bottom_left_layout.addWidget(self.new_conversation_name)
		self.new_conversation_button = QPushButton()
		self.new_conversation_button.setIcon(QIcon.fromTheme("list-add"))
		self.new_conversation_button.clicked.connect(self.new_conversation)
		self.bottom_left_layout.addWidget(self.new_conversation_button)
		self.left_panel.addLayout(self.bottom_left_layout)
		
		w = QWidget()
		w.setLayout(self.left_panel)
		self.splitter.addWidget(w)
		
		self.right_panel = QVBoxLayout()
		self.name_description_layout = QHBoxLayout()
		self.models_combobox = QComboBox()
		self.models_combobox.addItem("Select A Model...")
		self.models_combobox.addItems(Context.model_loader.model_names)
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
		
		self.name_description_layout.addSpacing(10)
		self.more_conversation_controls = QWidget()
		self.more_conversation_controls_layout = QHBoxLayout()
		self.more_conversation_controls.setLayout(self.more_conversation_controls_layout)
		self.right_panel.addWidget(self.more_conversation_controls)
		
		self.more_conversation_controls_toggle = QToolButton()
		self.name_description_layout.addWidget(self.more_conversation_controls_toggle)
		self.more_conversation_controls_toggle.setArrowType(Qt.RightArrow)
		self.more_conversation_controls_toggle.setCheckable(True)
		self.more_conversation_controls_toggle.setChecked(Context.settings.value("main/ShowMoreConversationControls", False, type=bool))
		def toggle_more_conversation_controls():
			self.more_conversation_controls.setVisible(self.more_conversation_controls_toggle.isChecked())
			if self.more_conversation_controls_toggle.isChecked():
				self.more_conversation_controls_toggle.setArrowType(Qt.DownArrow)
			else:
				self.more_conversation_controls_toggle.setArrowType(Qt.RightArrow)
			Context.settings.setValue("main/ShowMoreConversationControls", self.more_conversation_controls_toggle.isChecked())
		self.more_conversation_controls_toggle.clicked.connect(toggle_more_conversation_controls)
		toggle_more_conversation_controls()
		
		self.more_conversation_controls_layout.addWidget(QLabel("More Conversation Controls:"))
		
		self.chatUI = ChatUI()
		self.right_panel.addWidget(self.chatUI)
		self.chatUI.respond_to_conversation.connect(self.generate_ai_response)
		self.chatUI.stop_generating.connect(self.stop_generating)
		self.chatUI.conversation_view.regenerate_message.connect(self.regenerate)
		
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
		Context.conversation = conv
		Context.context_changed()
		return conv
	
	def toggle_settings_window(self):
		def get_settings_window_geometry():
			main_window_rect = self.frameGeometry()
			offset = 50
			x = main_window_rect.x() + offset
			y = main_window_rect.y() + offset
			width = main_window_rect.width() - offset
			height = main_window_rect.height() - offset
			return QRect(x, y, width, height)
		if self.settings_button.isChecked():
			self.settings_window.show()
			self.settings_window.raise_()
			self.settings_window.activateWindow()
			self.settings_window.setGeometry(get_settings_window_geometry())
		else:
			self.settings_window.close()
			
	def _name_description_confirm(self):
		if Context.conversation is None:
			return
		
		if Context.conversation.name != self.name_field.text() or Context.conversation.description != self.description_field.text():
			Context.conversation.name = self.name_field.text()
			Context.conversation.description = self.description_field.text()
			Context.conversation.last_modified = get_local_time()
			self.conversation_list_view._redraw_conversation(Context.conversation)
			self.engine.merge(Context.conversation)
	
	def search_name_description(self):
		search = self.search_field.text()
		if search == "":
			for conv in self.conversation_list_view.conversations.conversations:
				conv._show = True
		else:
			for conv in self.conversation_list_view.conversations.conversations:
				conv._show = search.lower() in conv.name.lower() or search.lower() in conv.description.lower()
		self.conversation_list_view._redraw_items()
		
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
			for conversation in self.conversations:
				conversation._show = False
				for message in (getattr(conversation, "message_sequence",[]) or []):
					if search.lower() in message.content.lower():
						conversation._show = True
			self.conversation_list_view._redraw_items()
	
	def read_settings(self):
		self.restoreGeometry(Context.settings.value("geometry", QByteArray()))

	def write_settings(self):
		Context.settings.setValue("geometry", self.saveGeometry())
	
	def closeEvent(self, event):
		self.write_settings()
		super().closeEvent(event)
	
	def stop_generating(self):
		self._should_generate = False
		
	def generate_ai_response(self, conversation:Conversation):
		Context.llm_generating = True
		Context.context_changed()
		
		self._should_generate = True
		start_str = Context.start_str
		max_tokens = self.chatUI.max_tokens
			
		def chat():
			print(f"chat:  {datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')}")
			response = self.llm.chat(conversation, start_str=start_str, stream=True, max_tokens=max_tokens)
			print(f"chat done:  {datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')}")
			conversation.add_message(response.message)
			print(f"message added:  {datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')}")
			while response.generate_more():
				print(f"generate more:  {datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')}")
				if not self._should_generate:
					response.stop_streaming()
					break
			print(f"generate more DONE:  {datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')}")
			print(f"AI said: {response.message.content}")
			return response.message
		
		self.task = BackgroundTask(chat)
		
		def finished():
			Context.llm_generating = False
			Context.context_changed()
		
		self.task.finished.connect(finished)
		self.task.start()
	
	def regenerate(self, message_source:ModelSource):
		if self.llm is None:
			return
				
		conv = self.chatUI.conversation_view.conversation
		self.chatUI.conversation_view.conversation = None
		
		conv.message_sequence = message_source.message_sequence
		self.chatUI.conversation_view.conversation = conv
		
		self.generate_ai_response(conv)
		
	def select_model(self, model_name:str):
		self.models_combobox.currentTextChanged.disconnect(self.select_model)
		if self.models_combobox.itemText(0) == "Select A Model...":
			self.models_combobox.removeItem(0)
			self.models_combobox.setEnabled(False)
		
		self.models_combobox.insertItem(0, ".  ")
		self.models_combobox.setCurrentIndex(0)
		
		def load_model():
			try:
				self.llm = Context.model_loader[model_name]
				self.llm.start()
				return True
			except Exception as e:
				print(f"Error loading model '{model_name}' with exception: {e}")
				return False
		
		self.task = BackgroundTask(load_model, 200)
		
		def animate():
			t = self.models_combobox.itemText(0)
			t = {
				".  " : " . ",
				" . " : "  .",
				"  ." : ".  "
			}[t]
			self.models_combobox.setItemText(0, t)
			
		def model_loaded():
			self.models_combobox.removeItem(0)
			if self.task.return_val:
				self.models_combobox.setCurrentText(model_name)
			else:
				self.models_combobox.insertItem(0, "Select A Model...")
				self.models_combobox.setCurrentIndex(0)
			self.models_combobox.currentTextChanged.connect(self.select_model)
			self.models_combobox.setEnabled(True)
		
		self.task.finished.connect(model_loaded)
		self.task.busy_indication.connect(animate)
		self.task.start()
		
Stopwatch.end_scope(log_statistics=False)
if __name__ == "__main__":
	Stopwatch("Load settings", log_statistics=False)
	app = QApplication(sys.argv)
	Context.settings = QSettings("Inventor2525", "AbstractAI")
	
	def get_default_storage_location():
		config_dir = os.path.expanduser("~/.config/AbstractAI/")
		if os.path.exists(config_dir):
			return os.path.join(config_dir, 'chats.db')
		return os.path.join(os.path.expanduser('~'), 'AbstractAI.db')

	parser = argparse.ArgumentParser(description='AbstractAI')
	
	parser.add_argument(
		'storage_location', nargs='?',
		default=Context.settings.value(
			"main/storage_location",
			get_default_storage_location(), 
			type=str
		),
		help='Path to SQLite database file (default: %(default)s)'
	)
	
	Context.args = parser.parse_args()
	Context.settings.setValue("main/storage_location", Context.args.storage_location)
	
	Stopwatch("Load models", log_statistics=False)
	models = {
		"Mistral": {
			"LoaderType": "LLamaCPP",
			"ModelPath": "/home/charlie/Projects/text-generation-webui/models/mistral-7b-instruct-v0.2.Q4_K_M.gguf",
			"Parameters": {}
		},
		"Mixtral": {
			"LoaderType": "LLamaCPP",
			"ModelPath": "/home/charlie/Projects/text-generation-webui/models/mixtral-8x7b-instruct-v0.1.Q4_K_M.gguf",
			"Parameters": { 
				"model": {
					"n_gpu_layers":0,
				}
			}
		},
		"GPT-3.5 Turbo": {
			"ModelName": "gpt-3.5-turbo",
			"LoaderType": "OpenAI",
			"Parameters": {},
			"APIKey": APIKeyGetter("OpenAI", Context.settings) #TODO: include this as a default: os.environ.get("OPENAI_API_KEY")
		},
		"GPT-4": {
			"ModelName": "gpt-4",
			"LoaderType": "OpenAI",
			"Parameters": {},
			"APIKey": APIKeyGetter("OpenAI", Context.settings) #TODO: include this as a default: os.environ.get("OPENAI_API_KEY")
		},
		"GPT-4 (OLD)" : {
			"ModelName": "gpt-4-0613",
			"LoaderType": "OpenAI",
			"Parameters": {},
			"APIKey": APIKeyGetter("OpenAI", Context.settings)
		}
	}
	Context.model_loader = ModelLoader(models)
	Stopwatch("Load window", log_statistics=False)
	window = Application()
	
	Stopwatch("Show window", log_statistics=False)
	window.show()
	Stopwatch.stop("Show window", log_statistics=False)
	Stopwatch.end_scope(log_statistics=False)
	Stopwatch.end_scope(log_statistics=False)
	sys.exit(app.exec_())