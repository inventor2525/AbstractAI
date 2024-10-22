from PyQt5.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QPushButton, 
                             QTextEdit, QApplication, QSizePolicy, QScrollBar)
from PyQt5.QtCore import Qt, QEventLoop
from AbstractAI.AppContext import AppContext
from AbstractAI.UI.ChatViews.ChatUI import ChatUI
from AbstractAI.Helpers.run_in_main_thread import run_in_main_thread
from AbstractAI.Model.Converse import Conversation, Message, Role, CallerInfo
from AbstractAI.Automation.Agent import Agent
from AbstractAI.Helpers.ResponseParsers import MarkdownCodeBlockInfo
from AbstractAI.UI.ChatViews.ConversationActionControl import ConversationAction
from AbstractAI.Model.Settings.OpenAI_TTS_Settings import OpenAI_TTS_Settings
from AbstractAI.TextToSpeech.TTS import OpenAI_TTS, TTSJob
from AbstractAI.Helpers.AudioPlayer import AudioPlayer
from openai import OpenAI
from pathlib import Path
from pydub import AudioSegment
import os
from datetime import datetime
import subprocess
import re
from typing import List, Tuple

class MobileWindow(QMainWindow):
    def __init__(self, chat_ui: ChatUI):
        super().__init__()
        self.chat_ui = chat_ui
        self.displaying_subprocess_output = False
        
        self.bash_blocks_count: int = 0
        self.current_bash_output: Tuple[int, str] = None
        self.user_selected_bash_outputs: List[Tuple[int, str]] = []
        self.init_ui()
        
        AppContext.context_changed.connect(self.on_context_changed)
        AppContext.conversation_selected.connect(self.on_conversation_changed)
        
        tts_settings = MobileWindow.load_tts_settings()
        self.tts = OpenAI_TTS(callback=self.tts_complete, settings=tts_settings)
        self.audio_player = AudioPlayer()
        
        self.playback_override_getter = None

    @staticmethod
    def load_tts_settings() -> OpenAI_TTS_Settings:
        if hasattr(MobileWindow, "tts_settings"):
            return MobileWindow.tts_settings
        settings = AppContext.engine.query(OpenAI_TTS_Settings).first()
        if settings is None:
            settings = OpenAI_TTS_Settings()
            AppContext.engine.merge(settings)
        MobileWindow.tts_settings = settings
        return settings

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
        controls_widget = QWidget()
        controls_layout = QVBoxLayout(controls_widget)
        controls_layout.setContentsMargins(0,0,0,0)
        controls_widget.setFixedWidth(200)
        
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
        
        self.send_with_tools_button = QPushButton("Send\n\\w\nTools")
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
        
        self.layout.addWidget(controls_widget)

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
        
        # Create a horizontal layout for Confirm, Skip, Play, and Add Result buttons
        button_layout = QHBoxLayout()
        
        self.confirm_button = QPushButton("Confirm")
        self.confirm_button.setFixedHeight(35)
        self.confirm_button.setVisible(False)
        button_layout.addWidget(self.confirm_button)
        
        self.add_result_button = QPushButton("Add Result")
        self.add_result_button.setFixedHeight(35)
        self.add_result_button.setVisible(False)
        self.add_result_button.clicked.connect(self.toggle_add_result)
        button_layout.addWidget(self.add_result_button)
        
        self.skip_button = QPushButton("Skip")
        self.skip_button.setFixedHeight(35)
        self.skip_button.setVisible(False)
        button_layout.addWidget(self.skip_button)
        
        self.play_button = QPushButton("Play")
        self.play_button.setFixedHeight(35)
        self.play_button.setVisible(True)
        self.play_button.clicked.connect(self.on_play_pressed)
        button_layout.addWidget(self.play_button)
        
        text_view_layout.addLayout(button_layout)
        
        self.layout.addLayout(text_view_layout)

    @run_in_main_thread
    def update_conversation_text(self):
        if self.displaying_subprocess_output:
            return

        conversation = AppContext.conversation
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
        if AppContext.transcriber.is_recording:
            self.record_button.setText("Stop Recording")
        else:
            self.record_button.setText("Start Recording")

    def send_message(self):
        if AppContext.conversation is not None and AppContext.main_agent is not None:
            self.chat_ui.on_action(ConversationAction.Send, AppContext.main_agent.llm)

    def send_message_with_tools(self):
        if AppContext.conversation is not None and AppContext.main_agent is not None:
            self.chat_ui.on_action(ConversationAction.Send, AppContext.main_agent)

    def do_it(self):
        if AppContext.conversation and AppContext.main_agent:
            self.displaying_subprocess_output = True
            self.user_selected_bash_outputs = []
            
            bash_script_count = 1
            last_message = AppContext.conversation[-1]
            
            for code_block in AppContext.main_agent.process_response(AppContext.conversation):
                self.current_bash_output = None
                self.text_view.clear()
                
                if code_block.path is not None:
                    self.text_view.append(f"Saving:\n{code_block.content}\n")
                    self.text_view.append("-" * 40 + "\n")
                    self.text_view.append(f"to file: {code_block.path}?\nConfirm to save, or Skip.")
                    
                    self.playback_override_getter = lambda path=code_block.path: f"Saving file to {self.format_path_for_speech(path)}"
                    
                    if self.wait_for_confirmation():
                        os.makedirs(os.path.dirname(code_block.path), exist_ok=True)
                        with open(code_block.path, 'w', encoding='utf-8') as file:
                            file.write(code_block.content)
                elif code_block.language == 'bash':
                    timestamp = datetime.now().strftime("%Y-%m-%d %H-%M-%S-%f")[:-3]
                    script_filename = f"{timestamp}_{str(last_message.get_primary_key())}_{bash_script_count}"
                    script_path = os.path.expanduser(f"~/ai_scripts/{script_filename}")
                    
                    os.makedirs(os.path.dirname(script_path), exist_ok=True)
                    with open(f"{script_path}.txt", 'w') as f:
                        f.write(code_block.content)
                    
                    self.text_view.append(f"Execute bash script:\n{code_block.content}\n")
                    self.text_view.append("-" * 40 + "\n")
                    self.text_view.append("Proceed with execution?")
                    
                    self.playback_override_getter = lambda content=code_block.content: self.summarize_for_tts(f"Bash script to execute: {content}")
                    
                    if self.wait_for_confirmation():
                        process = subprocess.Popen(
                            ['bash', '-c', code_block.content],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT,
                            text=True,
                            bufsize=1,
                            universal_newlines=True
                        )
                        
                        output = []
                        with open(f"{script_path}_output.txt", 'w') as output_file:
                            for line in process.stdout:
                                self.text_view.append(line)
                                output_file.write(line)
                                output.append(line)
                        
                        process.wait()
                        self.current_bash_output = (bash_script_count, ''.join(output))
                        self.text_view.append("-" * 40 + "\n")
                        self.text_view.append("Done!")
                        
                        self.playback_override_getter = lambda content=code_block.content, output=output: self.summarize_for_tts(f"Bash script executed: {content}\nOutput: {self.current_bash_output[1]}")
                        
                        self.add_result_button.setText("Add Result")
                        self.add_result_button.setVisible(True)
                        self.wait_for_continue()
                        self.add_result_button.setVisible(False)
                    
                    bash_script_count += 1
            self.current_bash_output = None
            self.bash_blocks_count = bash_script_count-1
            self.displaying_subprocess_output = False
            self.update_conversation_text()
            self.playback_override_getter = None
            
            if self.user_selected_bash_outputs:
                self.add_bash_outputs_to_conversation()
                
    def toggle_add_result(self):
        if not self.current_bash_output:
            return

        if self.add_result_button.text() == "Add Result":
            self.user_selected_bash_outputs.append(self.current_bash_output)
            self.add_result_button.setText("Remove Result")
        else:
            self.user_selected_bash_outputs = [output for output in self.user_selected_bash_outputs if output[0] != self.current_bash_output[0]]
            self.add_result_button.setText("Add Result")
            
    def add_bash_outputs_to_conversation(self):
        if not self.user_selected_bash_outputs:
            return
        
        content = None
        if self.bash_blocks_count>1 and len(self.user_selected_bash_outputs)>0:
            content = "This is the result of the bash scripts you ran (starting at block '1'):\n\n"
            for count, output in self.user_selected_bash_outputs:
                content += f"For block number {count}:\n```bash\n{output}\n```\n\n"
        elif self.bash_blocks_count==1 and len(self.user_selected_bash_outputs)==1:
            content = f"Your bash script returned:\n```bash\n{self.user_selected_bash_outputs[0][1]}```"
        if content:
            AppContext.conversation + (content, Role.System()) | CallerInfo.catch([0,1])
            self.update_conversation_text()
        
    def wait_for_confirmation(self) -> bool:
        self.confirm_button.setText("Confirm")
        self.confirm_button.setVisible(True)
        self.skip_button.setVisible(True)
        
        loop = QEventLoop()
        result = [False]
        
        def on_confirm():
            result[0] = True
            loop.quit()
        
        def on_skip():
            result[0] = False
            loop.quit()
        
        self.confirm_button.clicked.connect(on_confirm)
        self.skip_button.clicked.connect(on_skip)
        
        loop.exec_()
        
        self.confirm_button.clicked.disconnect(on_confirm)
        self.skip_button.clicked.disconnect(on_skip)
        
        self.confirm_button.setVisible(False)
        self.skip_button.setVisible(False)
        
        return result[0]
    
    def wait_for_continue(self):
        self.confirm_button.setText("Continue")
        self.confirm_button.setVisible(True)
        
        loop = QEventLoop()
        self.confirm_button.clicked.connect(loop.quit)
        loop.exec_()
        self.confirm_button.clicked.disconnect(loop.quit)
        self.confirm_button.setVisible(False)
        
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

    def on_play_pressed(self):
        if self.playback_override_getter:
            text = self.playback_override_getter()
        else:
            text = AppContext.conversation[-1].content if AppContext.conversation else self.chat_ui.input_field.toPlainText()
        
        if len(text)>0:
            self.tts.speak(text)

    @run_in_main_thread
    def tts_complete(self, job:TTSJob):
        self.audio_player.play(job.data.speech)
        
    def summarize_for_tts(self, text: str) -> str:
        conversation = Conversation("Summarizing for text-to-speech", "Summarize text for TTS") | CallerInfo.catch([0, 1])
        conversation + ("Please summarize this text and say it in a way in plain English that's clear and understandable as to be spoken by a text-to-speech program:", Role.System())
        conversation + (text, Role.User())
        
        response = AppContext.main_agent.llm.chat(conversation)
        conversation + response
        return response.content

    def format_path_for_speech(self, path: str) -> str:
        return path.replace(os.path.sep, " in ")