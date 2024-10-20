from AbstractAI.UI.Support._CommonImports import *
from AbstractAI.Helpers.run_in_main_thread import run_in_main_thread
from AbstractAI.AppContext import AppContext, UserSource, Conversation, Message, ModelSource, EditSource
from AbstractAI.Automation.Agent import Agent, AgentConfig
from enum import Enum

class ConversationAction(Enum):
	Add = "Add" # Adds the message in the text edit to the conversation (saving it to the db) and clears the text edit
	Send = "Send" # Same as Add but also sends the conversation to the AI
	Continue = "Continue" # Continues the AI's response from it's last message
	Reply = "Reply" # Replies to the last message in the conversation (this is useful when you manually build out a conversation and want the AI to respond to the last message you added)
	Insert = "Insert" # Inserts the message in the text edit above the selected message in the conversation view
	DoIt = "DoIt" # Sends the conversation to an instruction following agent
	Demo = "Demo" # Allows the user to demonstrate to the instruction following agent how to perform the instructions in the conversation
	Stop = "Stop" # Stops the AI from generating a response

class ConversationActionControl(QWidget):
	perform_action = pyqtSignal(ConversationAction)
	
	@property
	def should_auto_respond(self) -> bool:
		return not self.auto_respond_toggle.isChecked()
	
	def __init__(self, labels:Dict[ConversationAction, str] = {
		ConversationAction.Add: "Add Msg",
		ConversationAction.Send: "Send Msg",
		ConversationAction.Continue: "Continue >>",
		ConversationAction.Reply: "Reply To",
		ConversationAction.Insert: "Insert Above",
		ConversationAction.DoIt: "Do it!",#":media-playback-start:",
		ConversationAction.Demo: ":media-record:",
		ConversationAction.Stop: "Stop!"
	},
	descriptions:Dict[ConversationAction, str] = {
		ConversationAction.Add: "Adds the message in the text edit to the conversation (saving it to the db), and clears the text edit.",
		ConversationAction.Send: "Adds the message in the text edit to the conversation (saving it to the db), clears the text edit, and sends the conversation to the AI.",
		ConversationAction.Continue: "Continues the AI's response from the end of it's last message.",
		ConversationAction.Reply: "Replies to the last message in the conversation (this is useful when you manually build out a conversation and want the AI to respond to the last message you added).",
		ConversationAction.Insert: "Inserts the message in the text edit above the selected message in the conversation view.",
		ConversationAction.DoIt: "Sends the conversation to an instruction following agent.",
		ConversationAction.Demo: "Allows you to demonstrate to the instruction following agent how to perform the instructions in the conversation.",
		ConversationAction.Stop: "Stops the AI from generating a response."
	},
	instruction_tooltips:Dict[ConversationAction, str] = {
		ConversationAction.DoIt: "You need to load an instruction following agent and make sure there is some conversation (presumably containing instructions) loaded to use this feature which is currently not implemented.",
		ConversationAction.Send: "You need to load a model and type something in the new message text box to use this feature. You can load a model by selecting one from the dropdown in the top left of the chat view.",
		ConversationAction.Continue: "You need to load a model capable of accepting a start of message (usually, this is only open weight models run locally) and make sure there is a message with a model source at the end of the conversation to use this feature. You can load a model by selecting one from the dropdown in the top left of the chat view.",
		ConversationAction.Reply: "You need to load a model and make sure there is a message with a user source at the end of the conversation to use this feature. You can load a model by selecting one from the dropdown in the top left of the chat view."
	}):
		super().__init__()
		self.labels = labels
		self.descriptions = descriptions
		self.instruction_tooltips = instruction_tooltips
		
		#Context Views:
		self.selected_messages = []
		
		def conversation_changed():
			self.update_mode()
		def conversation_selected(prev_conversation:Conversation, new_conversation:Conversation):
			if prev_conversation is not None:
				prev_conversation.conversation_changed.disconnect(conversation_changed)
			if new_conversation:
				new_conversation.conversation_changed.connect(conversation_changed)
			self.selected_messages = []
		AppContext.conversation_selected.connect(conversation_selected)
		AppContext.context_changed.connect(self.update_mode)
		
		self._init_ui()
		
	def _init_ui(self):
		self.layout = QHBoxLayout()
		self.layout.setContentsMargins(0, 0, 0, 0)
		self.setLayout(self.layout)
		
		self.auto_respond_toggle = QToolButton()
		self.auto_respond_toggle.setCheckable(True)
		self.auto_respond_toggle.setChecked(False)
		self.auto_respond_toggle.setIcon(QIcon.fromTheme("insert-text"))
		self.auto_respond_toggle.setToolTip("Edit the conversation without automatic response when checked.")
		self.auto_respond_toggle.clicked.connect(self._on_auto_respond_toggle)
		self.layout.addWidget(self.auto_respond_toggle, alignment=Qt.AlignBottom)
		
		self.left_button = QPushButton("...")
		self.left_button.clicked.connect(self.onLeftButtonClicked)
		self.left_button.setFixedHeight(self.left_button.fontMetrics().height() + 4)
		self.left_button.setFixedWidth(self.left_button.height())
		# self.left_button.setStyleSheet("QPushButton {border: none; outline: none;}")
		self.layout.addWidget(self.left_button, alignment=Qt.AlignBottom)
		
		self.right_button = QPushButton("...")
		self.right_button.clicked.connect(self.onRightButtonClicked)
		self.layout.addWidget(self.right_button, alignment=Qt.AlignBottom)
	
	def _on_auto_respond_toggle(self):
		self.update_mode()
	
	def set_btn_mode(self, btn:QPushButton, action:ConversationAction, enabled:bool=True):
		if action is None:
			btn.setHidden(True)
		else:
			btn.setHidden(False)
			label = self.labels[action]
			if label.startswith(":") and label.endswith(":"):
				btn.setIcon(QIcon.fromTheme(label[1:-1]))
				btn.setText("")
			else:
				btn.setText(label)
				btn.setIcon(QIcon())
			if enabled or action not in self.instruction_tooltips:
				btn.setToolTip(self.descriptions[action])
			else:
				description = self.descriptions[action]
				instructions = self.instruction_tooltips[action]
				btn.setToolTip(f"{instructions} Once done, this button:\n\n{description}")
			btn.setEnabled(enabled)
		btn.action = action
	
	@run_in_main_thread
	def update_mode(self):
		if AppContext.llm_generating:
			self.set_btn_mode(self.left_button, None)
			self.set_btn_mode(self.right_button, ConversationAction.Stop)
			return
		
		def get_demo_do_it() -> Tuple[ConversationAction, bool]:
			if self.should_auto_respond:
				def should_display_DoIt():
					conv:Conversation = AppContext.conversation
					if conv is None or conv.source is None:
						return False
					if len(conv) == 0:
						return False
					if not conv.get_source(AgentConfig):
						return False
					return True
				return ConversationAction.DoIt, should_display_DoIt()
			else:
				return ConversationAction.Demo, False#True
		
		if len(self.selected_messages) == 1:
			self.set_btn_mode(self.left_button, *get_demo_do_it())
			self.set_btn_mode(self.right_button, ConversationAction.Insert)
		else:
			if self.should_auto_respond:
				self.set_btn_mode(self.left_button, *get_demo_do_it())
				if AppContext.new_message_has_text:
					self.set_btn_mode(self.right_button, ConversationAction.Send, enabled=AppContext.llm_loaded)
				else:
					if AppContext.conversation is None:
						self.set_btn_mode(self.right_button, ConversationAction.Send, enabled=False)
					elif len(AppContext.conversation) == 0:
						self.set_btn_mode(self.right_button, ConversationAction.Send, enabled=AppContext.llm_loaded)
					else:
						last_msg = AppContext.conversation[-1]
						model_source = last_msg.get_source(ModelSource, expand_edits=True)
						if model_source:
							self.set_btn_mode(self.right_button, ConversationAction.Continue, enabled=AppContext.llm_loaded)
						else:
							self.set_btn_mode(self.right_button, ConversationAction.Reply, enabled=AppContext.llm_loaded)
			else:
				self.set_btn_mode(self.left_button, *get_demo_do_it())
				self.set_btn_mode(self.right_button, ConversationAction.Add)
	
	def onLeftButtonClicked(self):
		self.perform_action.emit(self.left_button.action)
	
	def onRightButtonClicked(self):
		self.perform_action.emit(self.right_button.action)