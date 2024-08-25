from PyQt5.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QPushButton, 
                             QTextEdit, QApplication, QSizePolicy, QScrollBar)
from PyQt5.QtCore import Qt, QEventLoop
from AbstractAI.UI.Context import Context
from AbstractAI.UI.ChatViews.ChatUI import ChatUI
from AbstractAI.Helpers.run_in_main_thread import run_in_main_thread
from AbstractAI.Model.Converse import Conversation, Message
from AbstractAI.Automation.Agent import Agent
from AbstractAI.Helpers.ResponseParsers import MarkdownCodeBlockInfo
from AbstractAI.UI.ChatViews.ConversationActionControl import ConversationAction
import os
from datetime import datetime

class MobileWindow(QMainWindow):
    def __init__(self, chat_ui: ChatUI):
        super().__init__()
        self.chat_ui = chat_ui
        self.init_ui()
        self.displaying_subprocess_output = False
        
        Context.context_changed.connect(self.on_context_changed)
        Context.conversation_selected.connect(self.on_conversation_changed)

    def init_ui(self):
        self.setWindowTitle("Mobile Chat")
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        self.layout = QHBoxLayout()
        self.central_widget.setLayout(self.layout)
        
        self.init_controls()
        self.init_text_view()
        
        self.update_conversation_text()

    def init_controls(self):
        controls_layout = QVBoxLayout()
        
        # Record button
        self.record_button = QPushButton("Start Recording")
        self.record_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.record_button.clicked.connect(self.toggle_recording)
        controls_layout.addWidget(self.record_button)
        
        # Send buttons layout
        send_buttons_layout = QHBoxLayout()
        
        self.send_button = QPushButton("Send")
        self.send_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.send_button.clicked.connect(self.send_message)
        send_buttons_layout.addWidget(self.send_button)
        
        self.send_with_tools_button = QPushButton("Send with Tools")
        self.send_with_tools_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.send_with_tools_button.clicked.connect(self.send_message_with_tools)
        send_buttons_layout.addWidget(self.send_with_tools_button)
        
        controls_layout.addLayout(send_buttons_layout)
        
        # Do it button
        self.do_it_button = QPushButton("Do It!")
        self.do_it_button.setStyleSheet("background-color: red; color: white;")
        self.do_it_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.do_it_button.clicked.connect(self.do_it)
        controls_layout.addWidget(self.do_it_button)
        
        self.layout.addLayout(controls_layout)

    def init_text_view(self):
        text_view_layout = QVBoxLayout()
        
        self.text_view = QTextEdit()
        self.text_view.setReadOnly(True)
        
        # Create a custom scroll bar
        scroll_bar = QScrollBar(Qt.Vertical, self.text_view)
        scroll_bar.setStyleSheet("""
            QScrollBar:vertical {
                width: 30px;
            }
        """)
        self.text_view.setVerticalScrollBar(scroll_bar)
        
        text_view_layout.addWidget(self.text_view)
        
        self.continue_button = QPushButton("Continue")
        self.continue_button.setEnabled(False)
        text_view_layout.addWidget(self.continue_button)
        
        self.layout.addLayout(text_view_layout)

    @run_in_main_thread
    def update_conversation_text(self):
        if self.displaying_subprocess_output:
            return

        conversation = Context.conversation
        if conversation is None:
            self.text_view.clear()
            return

        text = ""
        for message in conversation:
            text += f"# {message.role}:\n"
            text += message.content + "\n"
            text += "\n---\n\n"
        
        # Append the content of the main input field
        main_input_content = self.chat_ui.input_field.toPlainText()
        if main_input_content:
            text += f"# User:\n{main_input_content}"

        self.text_view.setPlainText(text)
        scroll_bar = self.text_view.verticalScrollBar()
        scroll_bar.setValue(scroll_bar.maximum())

    def toggle_recording(self):
        self.chat_ui.toggle_recording()
        if self.chat_ui.transcription.is_recording:
            self.record_button.setText("Stop Recording")
        else:
            self.record_button.setText("Start Recording")

    def send_message(self):
        if Context.conversation is not None and Context.main_agent is not None:
            self.chat_ui.on_action(ConversationAction.Send, Context.main_agent.llm)

    def send_message_with_tools(self):
        if Context.conversation is not None and Context.main_agent is not None:
            self.chat_ui.on_action(ConversationAction.Send, Context.main_agent)

    def do_it(self):
        if Context.conversation and Context.main_agent:
            self.displaying_subprocess_output = True
            self.text_view.clear()
            
            bash_script_count = 1
            last_message = Context.conversation[-1]
            
            for code_block, process_getter in Context.main_agent.process_response(Context.conversation):
                self.text_view.append(f"# Code block:\n{code_block.content}\n")
                self.text_view.append("-" * 40 + "\n")
                
                if process_getter is not None:
                    timestamp = datetime.now().strftime("%Y-%m-%d %H-%M-%S-%f")[:-3]
                    script_filename = f"{timestamp}_{str(last_message.get_primary_key())}_{bash_script_count}"
                    script_path = os.path.expanduser(f"~/ai_scripts/{script_filename}")
                    
                    os.makedirs(os.path.dirname(script_path), exist_ok=True)
                    with open(f"{script_path}.txt", 'w') as f:
                        f.write(code_block.content)
                    
                    process = process_getter()
                    
                    with open(f"{script_path}_output.txt", 'w') as output_file:
                        for line in process.stdout:
                            self.text_view.append(line)
                            output_file.write(line)
                    
                    process.wait()
                    bash_script_count += 1
                elif code_block.path is not None:
                    self.text_view.append(f"Saving to file: {code_block.path}?\n")
                
                self.wait_for_continue()
            
            self.displaying_subprocess_output = False
            self.update_conversation_text()

    def wait_for_continue(self):
        self.continue_button.setEnabled(True)
        loop = QEventLoop()
        self.continue_button.clicked.connect(loop.quit)
        loop.exec_()
        self.continue_button.clicked.disconnect(loop.quit)
        self.continue_button.setEnabled(False)

    def on_context_changed(self):
        self.update_conversation_text()

    def on_conversation_changed(self, prev_conversation:Conversation, new_conversation:Conversation):
        if prev_conversation:
            prev_conversation.conversation_changed.disconnect(self.update_conversation_text)
        if new_conversation:
            new_conversation.conversation_changed.connect(self.update_conversation_text)
        self.update_conversation_text()

    def closeEvent(self, event):
        event.ignore()
        self.hide()