from AbstractAI.UI.Elements.TextEdit import TextEdit
from AbstractAI.UI.ChatViews.ConversationView import ConversationView
from AbstractAI.UI.ChatViews.MessageView_extras.RoleComboBox import RoleComboBox
from AbstractAI.UI.ChatViews.ConversationActionControl import ConversationActionControl, ConversationAction
from AbstractAI.UI.ChatViews.ConversationPicker import ConversationPicker
from AbstractAI.UI.Support._CommonImports import *
from AbstractAI.UI.Context import Context
from AbstractAI.Model.Converse import *
from AbstractAI.Model.Converse.MessageSources.FilesSource import ItemsModel
from AbstractAI.UI.Elements.FileSelector import FileSelectionWidget
from AbstractAI.Automation.Agent import Agent, AgentConfig
from copy import deepcopy

from AbstractAI.Helpers.AudioRecorder import AudioRecorder
from AbstractAI.Helpers.AudioPlayer import AudioPlayer
from AbstractAI.UI.Elements.RecordingIndicator import RecordingIndicator
from AbstractAI.UI.Support.KeyComboHandler import KeyComboHandler, KeyAction, KeyEvent
import os
import time
from datetime import datetime
import json

import os
from AbstractAI.Model.Settings.TTS_Settings import Hacky_Whisper_Settings

class Transcription:
	def __init__(self, output_folder, hacky_tts_settings :Hacky_Whisper_Settings):
		self.recorder = AudioRecorder()
		self.player = AudioPlayer()
		self.hacky_tts_settings = hacky_tts_settings
		
		if hacky_tts_settings.use_groq:
			self._ensure_groq_loaded()
		else:
			self._ensure_local_model_loaded()
			
		self.output_folder = output_folder
		self.is_recording = False
		self.last_recording = None
		self.last_file_name = None
		
		self.recording_indicator = None
	
	def _ensure_groq_loaded(self):
		if hasattr(self, "client"):
			return
		from groq import Groq
		try:
			self.client = Groq(api_key=self.hacky_tts_settings.groq_api_key)
		except Exception as e:
			print("Error loading groq whisper {e}")
		
	def _ensure_local_model_loaded(self):
		if hasattr(self, "model"):
			return
		from faster_whisper import WhisperModel
		try:
			self.model = WhisperModel(
				self.hacky_tts_settings.model_name, 
				device=self.hacky_tts_settings.device, 
				compute_type=self.hacky_tts_settings.compute_type
			)
		except Exception as e:
			print("Error loading local whisper {e}")
		
	def toggle_recording(self):
		if self.is_recording:
			self.stop_recording()
		else:
			self.start_recording()

	def start_recording(self):
		if self.recording_indicator:
			self.recording_indicator.is_recording = True
		self.recorder.start_recording()
		self.start_time = time.time()
		self.is_recording = True

	def stop_recording(self):
		if self.recording_indicator:
			self.recording_indicator.is_recording = False
		self.last_recording = self.recorder.stop_recording()
		self.is_recording = False
		
		self.last_file_name = f"{datetime.now().strftime('%Y-%m-%d %H-%M-%S.%f')[:-3]}"
		audio_file_path = os.path.join(self.output_folder, f"{self.last_file_name}.mp3")
		self.last_recording.export(audio_file_path, format="mp3")

	def transcribe_last_recording(self):
		if self.last_file_name is None:
			print("No recording to transcribe.")
			return
		if self.recording_indicator:
			self.recording_indicator.is_processing = True
		audio_file_path = os.path.join(self.output_folder, f"{self.last_file_name}.mp3")
		audio_length = self.last_recording.duration_seconds
		
		start_time = time.time()
		try:
			self._ensure_groq_loaded()
			with open(audio_file_path, "rb") as file:
				transcription = dict(self.client.audio.transcriptions.create(
				file=(audio_file_path, file.read()),
				model="whisper-large-v3",
				prompt="Specify context or spelling",  # Optional
				response_format="verbose_json",  # Optional
				language="en",  # Optional
				temperature=0.0  # Optional
				))
				end_time = time.time()
				
				transcription_time = end_time - start_time
				transcription_rate = transcription_time / audio_length

				full_text = transcription['text']

				transcription_data = {
					"raw":transcription,
					"full_text": full_text,
					"audio_length": audio_length,
					"transcription_time": transcription_time,
					"transcription_rate": transcription_rate
				}
		except:
			self._ensure_local_model_loaded()
			segments, info = self.model.transcribe(audio_file_path, beam_size=5)
			segments_list = list(segments)
			end_time = time.time()
			
			transcription_time = end_time - start_time
			transcription_rate = transcription_time / audio_length

			full_text = " ".join([segment.text for segment in segments_list])

			transcription_data = {
				"language": info.language,
				"language_probability": info.language_probability,
				"segments": [
					{
						"start": segment.start,
						"end": segment.end,
						"text": segment.text
					} for segment in segments_list
				],
				"full_text": full_text,
				"audio_length": audio_length,
				"transcription_time": transcription_time,
				"transcription_rate": transcription_rate
			}

		json_file_path = os.path.join(self.output_folder, f"{self.last_file_name}.json")
		with open(json_file_path, 'w', encoding='utf-8') as f:
			json.dump(transcription_data, f, ensure_ascii=False, indent=4)
		if self.recording_indicator:
			self.recording_indicator.is_processing = False
		return full_text, audio_length, transcription_time, transcription_rate

	def play_last_recording(self):
		if self.last_recording is not None:
			self.player.play(self.last_recording)
		else:
			print("No recording to play. Record something first.")
			
class ChatUI(QWidget):
	respond_to_conversation = pyqtSignal(Conversation)
	stop_generating = pyqtSignal()
	
	@property
	def conversation(self) -> Conversation:
		return self.conversation_view.conversation
	@conversation.setter
	def conversation(self, value:Conversation):
		self.conversation_view.conversation = value
	
	@property
	def start_str(self) -> str:
		return self.message_prefix_field.toPlainText()
	
	@property
	def max_tokens(self) -> Optional[int]:
		try:
			return int(self.max_tokens_field.toPlainText())
		except:
			self.max_tokens_field.setText("")
			None
	
	def __init__(self, conversation: Conversation = None, roles:List[str]=["Human", "Assistant", "System", "Files"], max_new_message_lines=10):
		super().__init__()		
		self.roles = roles
		self.roles_map = {
			"Human":Role.User(),
			"Assistant":Role.Assistant(),
			"System":Role.System(),
			"Files":Role.User()
		}
		
		self.caller = CallerInfo.catch([0,1])
		self.max_new_message_lines = max_new_message_lines
		self.num_lines = 0
		
		# Set up transcription
		hacky_tts_settings = Context.engine.query(Hacky_Whisper_Settings).first()
		if hacky_tts_settings is None:
			hacky_tts_settings = Hacky_Whisper_Settings()
			
		db_path = Context.settings.value("main/storage_location", "")
		db_dir = os.path.dirname(db_path)
		self.recordings_folder = os.path.join(db_dir, "recordings")
		os.makedirs(self.recordings_folder, exist_ok=True)
		self.transcription = Transcription(self.recordings_folder, hacky_tts_settings)
		
		self.init_ui(conversation)
		self.transcription.recording_indicator = self.recording_indicator
		
		# Set up key handler
		self.key_handler = KeyComboHandler(key_actions=[
			KeyAction(device_name="ThinkPad Extra Buttons", keycode='KEY_PROG1', key_event_type=KeyEvent.KEY_DOWN, action=self.toggle_recording),
			KeyAction(device_name="AT Translated Set 2 keyboard", keycode='KEY_CALC', key_event_type=KeyEvent.KEY_DOWN, action=self.toggle_recording),
			KeyAction(device_name="AT Translated Set 2 keyboard", keycode='KEY_RIGHTCTRL', key_event_type=KeyEvent.KEY_DOWN, action=self.toggle_recording),
			KeyAction(device_name="Apple, Inc Apple Keyboard", keycode='KEY_F19', key_event_type=KeyEvent.KEY_DOWN, action=self.toggle_recording)
		])

	def init_ui(self, conversation:Conversation = None):
		self.layout = QVBoxLayout()
		self.layout.setContentsMargins(0, 0, 0, 0)
		self.setLayout(self.layout)
		
		# Add the ConversationPicker
		self.conversation_picker = ConversationPicker()
		self.layout.addWidget(self.conversation_picker)
		
		# Create a list view to display the conversation:
		self.conversation_view = ConversationView(conversation)
		self.conversation_view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
		self.layout.addWidget(self.conversation_view)
		
		# Create a layout to hold the user input and send button:
		self.input_layout = QHBoxLayout()
		self.layout.addLayout(self.input_layout)
		
		# Create a layout to hold the advanced controls:
		self.advanced_controls = QWidget()
		self.advanced_controls_layout = QVBoxLayout()
		self.advanced_controls_layout.setContentsMargins(0, 0, 0, 0)
		self.advanced_controls.setLayout(self.advanced_controls_layout)
		self.layout.addWidget(self.advanced_controls)
		
		advanced_controls_header = QWidget()
		advanced_controls_header_layout = QHBoxLayout(advanced_controls_header)
		advanced_controls_header_layout.setContentsMargins(0, 0, 0, 0)
		advanced_controls_header_layout.addWidget(QLabel("Advanced Generation Controls:"))
		advanced_controls_header_layout.addStretch(1)
		send_to_switchboard_button = QPushButton("Send to Switchboard")
		send_to_switchboard_button.clicked.connect(self.send_to_switchboard)
		advanced_controls_header_layout.addWidget(send_to_switchboard_button)
		self.advanced_controls_layout.addWidget(advanced_controls_header)
		
		self.advanced_controls_layout.addWidget(QHLine())
		
		# Create a field to set the max tokens:
		self.message_prefix_field_h_layout = QHBoxLayout()
		self.message_prefix_field_h_layout.addWidget(QLabel("Max Tokens:"))
		self.max_tokens_field = TextEdit("Max Tokens Field", auto_save=True)
		self.max_tokens_field.setFixedHeight(25)
		self.max_tokens_field.setPlaceholderText("Max Tokens")
		self.message_prefix_field_h_layout.addWidget(self.max_tokens_field)
		self.advanced_controls_layout.addLayout(self.message_prefix_field_h_layout)
		
		# Create a field to set the message prefix:
		self.advanced_controls_layout.addWidget(QLabel("AI Message Prefix:"))
		self.message_prefix_field = TextEdit("AI message prefix field", auto_save=True)
		self.message_prefix_field.setWordWrapMode(QTextOption.WrapAtWordBoundaryOrAnywhere)
		self.message_prefix_field.setPlaceholderText("Type the start of the ai message here...")
		def adjust_advanced_controls_size():
			self.adjust_text_field_size(self.message_prefix_field)
			self.advanced_controls.setFixedHeight(self.advanced_controls_layout.sizeHint().height())
		self.message_prefix_field.textChanged.connect(adjust_advanced_controls_size)
		self.advanced_controls_layout.addWidget(self.message_prefix_field)
		adjust_advanced_controls_size()
		
		# Allow the user to select a role to send the message as:
		self.role_combobox = RoleComboBox(self.roles, default_value=self.roles[0])
		self.input_layout.addWidget(self.role_combobox, alignment=Qt.AlignBottom)
		
		# Create a text box to type the message:
		self.input_field = TextEdit("New Message Input Field", auto_save=True)
		self.input_field.setWordWrapMode(QTextOption.WrapAtWordBoundaryOrAnywhere)
		def input_field_changed():
			self.adjust_text_field_size(self.input_field)
			Context.new_message_has_text = bool(self.input_field.toPlainText())
			Context.context_changed()
		self.input_field.textChanged.connect(input_field_changed)
		self.input_field.textChanged.connect(self.clear_selection)
		self.input_field.setPlaceholderText("Type your message here...")
		self.input_field.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
		self.input_layout.addWidget(self.input_field, alignment=Qt.AlignBottom)
		self.input_field.setFocus()
		
		self.file_selector = FileSelectionWidget()
		self.input_layout.addWidget(self.file_selector)
		def role_changed():
			if self.role_combobox.currentText() == "Files":
				self.input_field.setHidden(True)
				self.file_selector.setHidden(False)
			else:
				self.input_field.setHidden(False)
				self.file_selector.setHidden(True)
		self.role_combobox.currentTextChanged.connect(role_changed)
		role_changed()
		
		# Create a button to toggle the advanced controls:
		self.advanced_controls_toggle = QToolButton()
		self.advanced_controls_toggle.setCheckable(True)
		self.advanced_controls_toggle.setChecked(Context.settings.value("ChatUI/ShowAdvancedControls", False, type=bool))
		# self.advanced_controls_toggle.setText("
		self.advanced_controls_toggle.setIcon(QIcon.fromTheme("preferences-system"))
		self.advanced_controls_toggle.setToolTip("Show advanced controls")
		def toggle_advanced_controls():
			Context.settings.setValue("ChatUI/ShowAdvancedControls", self.advanced_controls_toggle.isChecked())
			self.advanced_controls.setVisible(self.advanced_controls_toggle.isChecked())
		self.advanced_controls_toggle.clicked.connect(toggle_advanced_controls)
		self.input_layout.addWidget(self.advanced_controls_toggle, alignment=Qt.AlignBottom)
		toggle_advanced_controls()
		
		self.action_control = ConversationActionControl()
		self.action_control.perform_action.connect(self.on_action)
		def selection_changed():
			self.action_control.selected_messages = self.conversation_view.selected_messages
			self.action_control.update_mode()
		self.conversation_view.selection_changed.connect(selection_changed)
		self.input_layout.addWidget(self.action_control, alignment=Qt.AlignBottom)
		
		# Adjust the size of the bottom row to fit the input field:
		self.adjust_text_field_size(self.input_field)
		self.advanced_controls_toggle.setFixedHeight(self.input_field.height())
		self.action_control.setFixedHeight(self.input_field.height())
		self.role_combobox.setFixedHeight(self.input_field.height())
		
		# Add recording indicator
		self.recording_indicator = RecordingIndicator()
		self.recording_indicator.clicked.connect(self.toggle_recording)
		self.recording_indicator.show()
		
		self.recording_buttons_layout = QHBoxLayout()
		self.advanced_controls_layout.addLayout(self.recording_buttons_layout)
		# Add toggle recording button
		self.toggle_recording_button = QPushButton("Start Recording")
		self.toggle_recording_button.clicked.connect(self.toggle_recording)
		self.recording_buttons_layout.addWidget(self.toggle_recording_button, alignment=Qt.AlignBottom)

		# Add play last recording button
		self.play_button = QPushButton("Play Last Recording")
		self.play_button.setEnabled(False)
		self.play_button.clicked.connect(self.transcription.play_last_recording)
		self.recording_buttons_layout.addWidget(self.play_button, alignment=Qt.AlignBottom)

		# Add timer label
		self.timer_label = QLabel("Time: 0s")
		self.advanced_controls_layout.addWidget(self.timer_label, alignment=Qt.AlignBottom)

		# Set up timer
		self.timer = QTimer()
		self.timer.timeout.connect(self.update_timer)
		self.timer.start(100)  # Update every 100ms
		
		self.init_mobile_window()
		
	def send_to_switchboard(self):
		from AbstractAI.Automation.SwitchboardAgent import SwitchboardAgent
		user_message = self.input_field.toPlainText()
		SwitchboardAgent.call_switchboard(user_message)
		self.input_field.clear()
		
	def toggle_recording(self):
		self.transcription.toggle_recording()
		if self.transcription.is_recording:
			self.toggle_recording_button.setText("Stop Recording")
		else:
			self.play_button.setEnabled(True)
			self.toggle_recording_button.setText("Start Recording")
			full_text, audio_length, transcription_time, transcription_rate = self.transcription.transcribe_last_recording()
			stats_text = f"Recording time: {audio_length:.2f}s | "
			stats_text += f"Transcription time: {transcription_time:.2f}s | "
			stats_text += f"Transcription rate: {transcription_rate:.2f}s/s"
			self.timer_label.setText(stats_text)
			self.input_field.append(full_text)
			
	def update_timer(self):
		if self.transcription.is_recording:
			elapsed_time = time.time() - self.transcription.start_time
			self.timer_label.setText(f"Time: {elapsed_time:.1f}s")
	
	def clear_selection(self):
		self.conversation_view.clearSelection()
		
	def _create_message(self) -> Message:
		selected_role = self.role_combobox.currentText()
		new_message = Message(self.input_field.toPlainText())
		new_message.role = self.roles_map[selected_role]
		
		if selected_role == "Assistant":
			new_message | ModelSource(settings=None, message_sequence=self.conversation.message_sequence) | self.caller
		elif selected_role == "Files":
			items = ItemsModel(items=deepcopy(self.file_selector.items))
			items.new_id()
			new_message | FilesSource(items=items) | self.caller
			new_message.content = new_message.source.load()
		else:
			new_message | Context.user_source
		return new_message
	
	def _add_message(self):
		new_message = self._create_message()
		self.conversation.add_message(new_message)
		
		selected_role = self.role_combobox.currentText()
		if selected_role != "Files":
			self.input_field.clear()
		
	
	def on_action(self, action:ConversationAction):
		if action == ConversationAction.Add:
			self._add_message()
		elif action == ConversationAction.Insert:
			new_message = self._create_message()
			self.conversation.insert_message(new_message, self.conversation_view.selected_messages[0])
			self.input_field.clear()
			
		elif action == ConversationAction.Send:
			Context.start_str = self.start_str
			self._add_message()
			self.respond_to_conversation.emit(self.conversation)
		elif action == ConversationAction.Reply:
			Context.start_str = self.start_str
			self.respond_to_conversation.emit(self.conversation)
		elif action == ConversationAction.Continue:
			Context.start_str = self.conversation[-1].content
			self.conversation.remove_message(self.conversation[-1], silent=True)
			self.respond_to_conversation.emit(self.conversation)
			
		elif action == ConversationAction.Stop:
			self.stop_generating.emit()
			
		elif action == ConversationAction.Demo:
			raise NotImplementedError("Demo not implemented")
		elif action == ConversationAction.DoIt:
			agent_config:AgentConfig = Context.conversation.source
			agent_config.agent.process_response(Context.conversation)
	
	def keyPressEvent(self, event):
		if event.key() == Qt.Key_Enter and event.modifiers() == Qt.ControlModifier:
			self.send_button.click()
		else:
			super().keyPressEvent(event)
	
	def adjust_text_field_size(self, text_field:QTextEdit=None):
		"""Adjust the height of the input field to fit the text up to max lines"""
		content_height = max(text_field.document().size().height(), text_field.fontMetrics().lineSpacing()+text_field.document().documentMargin()*2)
		content_margin_sum = + text_field.contentsMargins().top() + text_field.contentsMargins().bottom()
		
		max_height = text_field.fontMetrics().lineSpacing()*self.max_new_message_lines + text_field.document().documentMargin()*2
		
		new_height = min(content_height, max_height) + content_margin_sum
		text_field.setFixedHeight(int(new_height))
		
	# Add this to the ChatUI class
	def init_mobile_window(self):
		from AbstractAI.UI.Windows.MobileWindow import MobileWindow
		self.mobile_window = MobileWindow(self)
		mobile_window_button = QPushButton("Open Mobile Version")
		mobile_window_button.clicked.connect(self.show_mobile_window)
		self.advanced_controls_layout.insertWidget(1, mobile_window_button)

	def show_mobile_window(self):
		self.mobile_window.show()
		self.mobile_window.raise_()
		self.mobile_window.activateWindow()