from PyQt5.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QPushButton, 
                             QTextEdit, QApplication, QSizePolicy)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QColor
from AbstractAI.UI.Context import Context
from AbstractAI.UI.ChatViews.ChatUI import ChatUI
from AbstractAI.Helpers.run_in_main_thread import run_in_main_thread
from AbstractAI.Model.Converse import Conversation, Message
from AbstractAI.Automation.Agent import Agent
import subprocess
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
        self.record_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)#TODO: do this for all the buttons
        self.record_button.clicked.connect(self.toggle_recording)
        controls_layout.addWidget(self.record_button)
        
        # Send buttons layout
        send_buttons_layout = QHBoxLayout()
        
        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self.send_message)
        send_buttons_layout.addWidget(self.send_button)
        
        self.send_with_tools_button = QPushButton("Send with Tools")
        self.send_with_tools_button.clicked.connect(self.send_message_with_tools)
        send_buttons_layout.addWidget(self.send_with_tools_button)
        
        controls_layout.addLayout(send_buttons_layout)
        
        # Do it button
        self.do_it_button = QPushButton("Do It!")
        self.do_it_button.setStyleSheet("background-color: red; color: white;")
        self.do_it_button.clicked.connect(self.do_it)
        controls_layout.addWidget(self.do_it_button)
        
        self.layout.addLayout(controls_layout)

    def init_text_view(self):
        self.text_view = QTextEdit() #TODO:scroll bar needs to be very large
        self.text_view.setReadOnly(True)
        self.layout.addWidget(self.text_view)

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

    def toggle_recording(self):
        self.chat_ui.toggle_recording()
        if self.chat_ui.transcription.is_recording:
            self.record_button.setText("Start Recording")
        else:
            self.record_button.setText("Stop Recording")

    def send_message(self):
        if Context.conversation and Context.main_agent:
            llm = Context.main_agent.llm
            llm.chat(Context.conversation) #this needs to use send in chat ui logic

    def send_message_with_tools(self):
        if Context.conversation and Context.main_agent:
            Context.main_agent.chat(Context.conversation)#same, but needs added message in chat

    def do_it(self):
        if Context.conversation and Context.main_agent:
            self.displaying_subprocess_output = True
            self.text_view.clear()
            
            last_message = Context.conversation[-1]
            message_id = last_message.get_primary_key()
            
            # Extract and run bash blocks
            bash_blocks = self.extract_bash_blocks(last_message.content)
            for i, bash_block in enumerate(bash_blocks, 1):
                timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")[:-3]
                script_filename = f"{timestamp}_{message_id}_{i}"
                script_path = os.path.expanduser(f"~/ai_scripts/{script_filename}")
                
                os.makedirs(os.path.dirname(script_path), exist_ok=True)
                
                with open(script_path, 'w') as f:
                    f.write(bash_block)
                
                output_filename = f"{script_filename}_output"
                output_path = os.path.expanduser(f"~/ai_scripts/{output_filename}")
                
                self.text_view.append(f"Running bash block {i}:\n{'-' * 40}\n")
                
                process = subprocess.Popen(['bash', script_path], 
                                           stdout=subprocess.PIPE, 
                                           stderr=subprocess.STDOUT, 
                                           text=True, 
                                           bufsize=1, 
                                           universal_newlines=True)
                
                with open(output_path, 'w') as output_file:
                    for line in process.stdout:
                        self.text_view.append(line)
                        output_file.write(line)
                
                process.wait()
                #TODO: pause here waiting for user input to continue, also the output should go into the conversation optionally, buttons under text view?
            
            self.displaying_subprocess_output = False
            self.update_conversation_text()

    def extract_bash_blocks(self, content):
        # This is a simple implementation. You might need to adjust it based on your exact markdown format.
        bash_blocks = []
        lines = content.split('\n')
        in_bash_block = False
        current_block = []

        for line in lines:
            if line.strip() == '```bash':
                in_bash_block = True
            elif line.strip() == '```' and in_bash_block:
                in_bash_block = False
                bash_blocks.append('\n'.join(current_block))
                current_block = []
            elif in_bash_block:
                current_block.append(line)

        return bash_blocks

    def on_context_changed(self):
        self.update_conversation_text()

    def on_conversation_changed(self, prev_conversation, new_conversation):
        if new_conversation:
            new_conversation.conversation_changed.connect(self.update_conversation_text)
        self.update_conversation_text()

    def closeEvent(self, event):
        event.ignore()
        self.hide()