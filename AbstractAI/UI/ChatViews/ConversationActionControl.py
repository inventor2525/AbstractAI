from AbstractAI.UI.Support._CommonImports import *
from AbstractAI.Helpers.run_in_main_thread import run_in_main_thread
from AbstractAI.UI.Context import Context, UserSource, Conversation, Message, ModelSource
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
		ConversationAction.DoIt: ":media-record:",
		ConversationAction.Demo: ":media-playback-start:",
		ConversationAction.Stop: "Stop!"
	},
	descriptions:Dict[ConversationAction, str] = {
		ConversationAction.Add: "Adds the message in the text edit to the conversation (saving it to the db), and clears the text edit.",
		ConversationAction.Send: "Adds the message in the text edit to the conversation (saving it to the db), clears the text edit, and sends the conversation to the AI.",
		ConversationAction.Continue: "Continues the AI's response from the end of it's last message.",
		ConversationAction.Reply: "Replies to the last message in the conversation (this is useful when you manually build out a conversation and want the AI to respond to the last message you added).",
		ConversationAction.Insert: "Inserts the message in the text edit above the selected message in the conversation view.",
		ConversationAction.DoIt: "Sends the conversation to an instruction following agent.",
		ConversationAction.Demo: "Allows the user to demonstrate to the instruction following agent how to perform the instructions in the conversation.",
		ConversationAction.Stop: "Stops the AI from generating a response."
	},
	instruction_tooltips:Dict[ConversationAction, str] = {
		ConversationAction.DoIt: "You need to load an instruction following agent and make sure there is some conversation (presumably containing instructions) loaded to use this feature which is currently not implemented.",
		ConversationAction.Send: "You need to load a model and type something in the new message text box to use this feature. You can load a model by selecting one from the dropdown in the top left of the chat view.",
		ConversationAction.Continue: "You need to load a model and make sure there is a message with a model source at the end of the conversation to use this feature. You can load a model by selecting one from the dropdown in the top left of the chat view.",
		ConversationAction.Reply: "You need to load a model and make sure there is a message with a user source at the end of the conversation to use this feature. You can load a model by selecting one from the dropdown in the top left of the chat view."
	}):
		super().__init__()
		self.labels = labels
		self.descriptions = descriptions
		self.instruction_tooltips = instruction_tooltips
		
		#Context Views:
		self.has_instruction_agent = False
		self.messages_selected = []
		
		def conversation_changed():
			self._update_mode()
		def conversation_selected(prev_conversation:Conversation, new_conversation:Conversation):
			if prev_conversation is not None:
				prev_conversation.conversation_changed.disconnect(conversation_changed)
			new_conversation.conversation_changed.connect(conversation_changed)
		Context.conversation_selected.connect(conversation_selected)
		Context.context_changed.connect(self._update_mode)
		
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
		self.left_button.setStyleSheet("QPushButton {border: none; outline: none;}")
		self.layout.addWidget(self.left_button, alignment=Qt.AlignBottom)
		
		self.right_button = QPushButton("...")
		self.right_button.clicked.connect(self.onRightButtonClicked)
		self.layout.addWidget(self.right_button, alignment=Qt.AlignBottom)
	
	def _on_auto_respond_toggle(self):
		self._update_mode()
	
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
	def _update_mode(self):
		if Context.llm_generating:
			self.set_btn_mode(self.left_button, None)
			self.set_btn_mode(self.right_button, ConversationAction.Stop)
			return
		
		def get_demo_do_it() -> Tuple[ConversationAction, bool]:
			if self.should_auto_respond:
				conversation_empty = Context.conversation is None or len(Context.conversation) == 0
				return ConversationAction.DoIt, False#self.has_instruction_agent and not conversation_empty
			else:
				return ConversationAction.Demo, False#True
		
		if len(self.messages_selected) == 1:
			self.set_btn_mode(self.left_button, *get_demo_do_it())
			self.set_btn_mode(self.right_button, ConversationAction.Insert)
		else:
			if self.should_auto_respond:
				self.set_btn_mode(self.left_button, *get_demo_do_it())
				if Context.new_message_has_text:
					self.set_btn_mode(self.right_button, ConversationAction.Send, enabled=Context.llm_loaded)
				else:
					if len(Context.conversation) == 0:
						self.set_btn_mode(self.right_button, ConversationAction.Send, enabled=Context.llm_loaded)
					elif isinstance(Context.conversation[-1].source, ModelSource):
						self.set_btn_mode(self.right_button, ConversationAction.Continue, enabled=Context.llm_loaded)
					else:
						self.set_btn_mode(self.right_button, ConversationAction.Reply, enabled=Context.llm_loaded)
			else:
				self.set_btn_mode(self.left_button, *get_demo_do_it())
				self.set_btn_mode(self.right_button, ConversationAction.Add)
	
	def onLeftButtonClicked(self):
		self.perform_action.emit(self.left_button.action)
	
	def onRightButtonClicked(self):
		self.perform_action.emit(self.right_button.action)