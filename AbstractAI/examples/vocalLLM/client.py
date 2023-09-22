import sys
import argparse
import requests
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QTextEdit, QLabel, QPushButton, QHBoxLayout, QWidget
from AbstractAI.Helpers.AudioRecorder import AudioRecorder
from AbstractAI.SpeechToText.STT_Client import STT_Client
from AbstractAI.TextToSpeech.RemoteTTS import RemoteTTS
from AbstractAI.Helpers.AudioPlayer import *
from pydub.exceptions import CouldntDecodeError

class Application(QMainWindow):
	def __init__(self, host, port):
		super().__init__()

		self.host = host
		self.port = port

		self.recorder = AudioRecorder()
		self.stt = STT_Client(host, port)

		self.tts = RemoteTTS(host, port)
		self.audio_player = AudioPlayer()
		
		self.gui_init()

	def on_record_button_press(self):
		self.recorder.start_recording()

	def on_record_button_release(self):
		file_name = 'temp.mp3'
		audio_segment = self.recorder.stop_recording()
		audio_segment.export(file_name, format="mp3")
		result = self.stt.transcribe_str(file_name)
		self.you_text_edit.setText(result)
		self.on_send_button_click()

	def on_send_button_click(self):
		#Get the AI's response to user input:
		user_text = self.you_text_edit.toPlainText()
		response = requests.post(f'{self.host}:{self.port}/llm', json={'text': user_text})
		try:
			ai_response_text = response.json()['response']
			
			#Set the text output box contents:
			self.ai_response_text_edit.setText(ai_response_text)
			
			#Text to speech and play it:
			try:
				audio_segment = self.tts.text_to_speech(ai_response_text)
				self.audio_player.play(audio_segment)
			except:
				print("Decoding failed. The audio file may be corrupted or incorrectly formatted.")

		except requests.exceptions.JSONDecodeError:
			self.ai_response_text_edit.setText(f"Invalid response from server \"{response}\".")

	def gui_init(self):
		central_widget = QWidget()
		layout = QVBoxLayout()

		you_label = QLabel("You:")
		layout.addWidget(you_label)
		self.you_text_edit = QTextEdit()
		layout.addWidget(self.you_text_edit)

		space_label = QLabel()
		space_label.setFixedHeight(20)
		layout.addWidget(space_label)

		ai_response_label = QLabel("AI Response:")
		layout.addWidget(ai_response_label)
		self.ai_response_text_edit = QTextEdit()
		self.ai_response_text_edit.setReadOnly(True)
		layout.addWidget(self.ai_response_text_edit)

		buttons_layout = QHBoxLayout()
		record_button = QPushButton('Hold to record')
		record_button.pressed.connect(self.on_record_button_press)
		record_button.released.connect(self.on_record_button_release)
		buttons_layout.addWidget(record_button)
		send_button = QPushButton('Send')
		send_button.clicked.connect(self.on_send_button_click)
		buttons_layout.addWidget(send_button)

		layout.addLayout(buttons_layout)
		central_widget.setLayout(layout)
		self.setCentralWidget(central_widget)

		self.show()

if __name__ == "__main__":
	parser = argparse.ArgumentParser(description='Remote Speech-to-Text Client')
	parser.add_argument('host', type=str, help='The server\'s IP address or hostname (e.g., \'localhost\' or \'0.0.0.0\').')
	parser.add_argument('port', type=int, help='The port number on which the server is running (e.g., 8000).', default=8000)
	args = parser.parse_args()

	app = QApplication(sys.argv)
	window = Application(args.host, args.port)
	window.show()
	sys.exit(app.exec_())
