from AbstractAI.Helpers.Stopwatch import Stopwatch
import traceback
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
from AbstractAI.UI.Context import Context, MainAgent
from AbstractAI.UI.Windows.Settings import SettingsWindow, SettingItem

Stopwatch("Setting Models", log_statistics=False)
from AbstractAI.Model.Settings.LLMSettings import *
llm_settings_types = LLMSettings.load_subclasses()
from ClassyFlaskDB.new.AudioTranscoder import AudioTranscoder
from AbstractAI.Helpers.Jobs import *
from AbstractAI.UI.Windows.JobsUI import *
from AbstractAI.UI.Windows.MobileWindow import MobileWindow, OpenAI_TTS_Settings

from AbstractAI.LLMs.LLM import LLM
from AbstractAI.Automation.Agent import Agent, AgentConfig

Stopwatch("DATAEngine", log_statistics=False)
from ClassyFlaskDB.new.SQLStorageEngine import SQLStorageEngine

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
		self.llm : LLM = None
		
		Stopwatch.new_scope()
		self.setWindowTitle("AbstractAI")
		self.app = QApplication.instance()
		Stopwatch("Connect to database", log_statistics=False)
		
		self.settings_window = SettingsWindow()
		Context.engine = SQLStorageEngine(f"sqlite:///new_engine_test1.db", DATA)#{Context.args.storage_location}", DATA)
		
		self.llmConfigs = Context.engine.query(LLMConfigs).first()
		
		if self.llmConfigs is None:
			self.llmConfigs = LLMConfigs()
		
		# Set up transcription
		hacky_tts_settings = Context.engine.query(Hacky_Whisper_Settings).first()
		if hacky_tts_settings is None:
			hacky_tts_settings = Hacky_Whisper_Settings()
		
		Context.transcriber = Transcriber(hacky_tts_settings)
		self.init_settings()
		
		# Create a user:
		Context.user_source = UserSource() | CallerInfo.catch([0])
		
		Stopwatch("Load conversations", log_statistics=False)
		self.conversations = ConversationCollection.all_from_engine(Context.engine)
		
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
			if new_conversation:
				self.name_field.setEnabled(True)
				self.description_field.setEnabled(True)
				self.name_field.setText(new_conversation.name)
				self.description_field.setText(new_conversation.description)
			else:
				self.name_field.setEnabled(False)
				self.description_field.setEnabled(False)
				self.name_field.setText("")
				self.description_field.setText("")
			self.chatUI.conversation = new_conversation
		Context.conversation_selected.connect(conversation_selected)
		Context.conversation = self.new_conversation()
		Context.context_changed()
		
		self.read_settings()
		
		Context.main_agent = MainAgent()
		
		Context.jobs = Context.engine.query(Jobs).first()
		if Context.jobs is None:
			Context.jobs = Jobs()
		def save_jobs():
			with Context.jobs._lock:
				Context.engine.merge(Context.jobs)
		self.app.aboutToQuit.connect(save_jobs)
		self.app.aboutToQuit.connect(Context.transcriber.recorder.stop_listening)
		self.app.aboutToQuit.connect(Context.jobs.stop)
		Context.jobs.changed.connect(save_jobs)
		
		Stopwatch.end_scope(log_statistics=False)
		
		self.jobs_window = JobsWindow(Context.jobs)
		jobs_window_button = QPushButton("Open Jobs List")
		jobs_window_button.clicked.connect(self.open_jobs_list)
		self.chatUI.advanced_controls_header_layout.insertWidget(2, jobs_window_button)
		Context.jobs.start()
	
	def open_jobs_list(self):
		self.jobs_window.show()
		self.jobs_window.raise_()
		self.jobs_window.activateWindow()
		
	def init_settings(self):
		def settings_changed(path:str):
			if "Models/" in path:
				self.update_models_dict()
		self.settings_window.settingsChanged.connect(settings_changed)
		
		def add_model(model:LLMSettings):
			model_type_name = type(model).ui_name()
			self.settings_window.addSettingItem(SettingItem(
				model,
				f"Models/{model_type_name}/"+"{user_model_name}",
				excluded_fields=["auto_id", "id"]
			))
			
		def create_model_view():
			widget = QWidget()
			layout = QHBoxLayout()
			widget.setLayout(layout)
			
			model_type_picker = QComboBox()
			model_type_picker.addItems(llm_settings_types.keys())
			layout.addWidget(model_type_picker)
			
			def create_clicked():
				model_type = llm_settings_types[model_type_picker.currentText()]
				model = model_type()
				self.llmConfigs.models.append(model)
				add_model(model)
				
			create_button = QPushButton("Create")
			create_button.clicked.connect(create_clicked)
			create_button.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
			layout.addWidget(create_button)
			return widget
			
		self.settings_window.addSettingItem(SettingItem(
			self.llmConfigs,
			"Models",
			view_factories=[
				("Create Model", create_model_view)
			],
			excluded_fields=["id", "models", "auto_id"]
		))
		
		# Add OpenAI TTS settings
		self.settings_window.addSettingItem(SettingItem(
			MobileWindow.load_tts_settings(),
			"OpenAI TTS Settings",
			excluded_fields=["auto_id", "id"]
		))
	
		for model in self.llmConfigs.models:
			add_model(model)
			
		def save_settings():
			for model in self.llmConfigs.models:
				model.new_id(True)
			Context.engine.merge(self.llmConfigs)
			Context.engine.merge(Context.transcriber.hacky_tts_settings)
			Context.engine.merge(MobileWindow.load_tts_settings())
		self.settings_window.settingsSaved.connect(save_settings)
		
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
		self.models_combobox.beingUpdated = False
		self.update_models_dict()
		self.models_combobox.currentIndexChanged.connect(self._current_model_selection_changed)
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
		
		self.settings_window.addSettingItem(SettingItem(
			Context.transcriber.hacky_tts_settings,
			"TTS_Settings",
			excluded_fields=["auto_id"]
		))
		
		w = QWidget()
		w.setLayout(self.right_panel)
		self.splitter.addWidget(w)
		
		# Make the left panel keep its size:
		self.splitter.setStretchFactor(0, 0)
		self.splitter.setStretchFactor(1, 1)
		self.setCentralWidget(self.splitter)
	
	def format_model_name(self, model):
		return f"{model.__ui_name__}: {model.user_model_name}"
	
	def update_models_dict(self):
		self.models_combobox.beingUpdated = True
		self.models_combobox.clear()
		self.models_by_users_name = {}
		
		if self.llm is None:
			self.models_combobox.addItem("Select A Model...")
			
		color_counter = 0
		default_background_color = "white"
		alternate_background_color = "lightgrey"
		prev_ui_name = None
		for model in sorted(self.llmConfigs.models, key=self.format_model_name):
			self.models_by_users_name[model.user_model_name] = model
			if prev_ui_name is None:
				prev_ui_name = model.__ui_name__
			if not(prev_ui_name == model.__ui_name__):
				prev_ui_name = model.__ui_name__
				color_counter += 1
			item_text = self.format_model_name(model)
			self.models_combobox.addItem(item_text)
			
			if color_counter % 2 == 0:
				background_color = default_background_color
			else:
				background_color = alternate_background_color
			
			item = self.models_combobox.model().item(self.models_combobox.count() - 1)
			item.setBackground(QColor(background_color))
			item.setData(model, Qt.UserRole)
			
		if self.llm is not None:
			current_model_name = self.llm.settings.user_model_name
			for i in range(self.models_combobox.count()):
				if self.models_combobox.itemText(i) == self.format_model_name(self.llm.settings._copy_source_):
					self.models_combobox.setCurrentIndex(i)
					break
		self.models_combobox.beingUpdated = False
		
	def new_conversation(self):
		name = self.new_conversation_name.text()
		if name == "":
			name = "New Conversation"
		conv = Conversation(name, f"A conversation created at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}") | Context.user_source
		self.conversations.append(conv)
		Context.active_conversations.clear()
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
			Context.engine.merge(Context.conversation, persist=True)
	
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
	
	def stop_generating(self):
		self._should_generate = False
		
	def generate_ai_response(self, conversation:Conversation, conversable:Optional[Conversable] = None):
		Context.llm_generating = True
		Context.context_changed()
		
		self._should_generate = True
		start_str = Context.start_str
		max_tokens = self.chatUI.max_tokens
			
		def chat(conversable:Conversable=conversable):
			#Determine if this conversation is with an agent,
			#or the llm the user has chosen to chat with:
			if conversable is None:
				conversable = AgentConfig.get_agent(conversation)
				if conversable is None:
					conversable = self.llm
			response = conversable.chat(conversation, start_str=start_str, stream=True, max_tokens=max_tokens)
			conversation.add_message(response)
			while conversable.continue_message(response):
				response.emit_changed()
				if not self._should_generate:
					conversable.stop_message(response)
					break
		
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
	
	def _current_model_selection_changed(self, index: int):
		if self.models_combobox.beingUpdated:
			return
		model = self.models_combobox.model()
		q_index = model.index(index, 0)
		current_item = model.itemFromIndex(q_index)
		self.select_model(current_item.data(Qt.UserRole))
		
	def select_model(self, model:LLMSettings):
		# if model.__ui_name__ is "HuggingFace":
		# 	QMessageBox.critical(None, "Error", "Hugging Face models are currently broken in the UI.")
		# 	return
		
		self.models_combobox.currentIndexChanged.disconnect(self._current_model_selection_changed)
		if self.models_combobox.itemText(0) == "Select A Model...":
			self.models_combobox.removeItem(0)
			self.models_combobox.setEnabled(False)
		
		self.models_combobox.insertItem(0, ".  ")
		self.models_combobox.setCurrentIndex(0)
		
		def load_model():
			try:
				self.llm = model.load()
				self.llm.start()
				return True
			except Exception as e:
				print(f"Error loading model '{model.user_model_name}' with exception: {e}")
				print("Stack trace:")
				traceback.print_exc()
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
				self.models_combobox.setCurrentText(self.format_model_name(self.llm.settings))           
			else:
				self.models_combobox.insertItem(0, "Select A Model...")
				self.models_combobox.setCurrentIndex(0)
			self.models_combobox.currentIndexChanged.connect(self._current_model_selection_changed)
			self.models_combobox.setEnabled(True)
		
		self.task.finished.connect(model_loaded)
		self.task.busy_indication.connect(animate)
		self.task.start()
		
	def closeEvent(self, event):
		Context.transcriber.recorder.stop_listening()
		self.write_settings()
		QApplication.quit()
		
Stopwatch.end_scope(log_statistics=False)
if __name__ == "__main__":
	Stopwatch("Load settings", log_statistics=False)
	app = QApplication(sys.argv)
	qss_path = os.path.join(os.path.dirname(__file__), "Styles", "AbstractAI.qss")
	app.setStyle("Fusion")
	with open(qss_path, "r") as f:
		app.setStyleSheet(f.read())
		
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
	
	# new model loading code:
	Stopwatch("Load window", log_statistics=False)
	window = Application()
	
	Stopwatch("Show window", log_statistics=False)
	window.show()
	Stopwatch.stop("Show window", log_statistics=False)
	Stopwatch.end_scope(log_statistics=False)
	Stopwatch.end_scope(log_statistics=False)
	sys.exit(app.exec_())