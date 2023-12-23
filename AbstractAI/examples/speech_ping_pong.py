from AbstractAI.Remote.client import System

from PyQt5.QtWidgets import QApplication, QPushButton, QVBoxLayout, QWidget, QLabel
from AbstractAI.Helpers.AudioRecorder import *
from AbstractAI.Helpers.AudioPlayer import *

recorder = AudioRecorder()
player = AudioPlayer()

def on_button_press():
	recorder.start_recording()

def on_button_release():
	audio_segment = recorder.stop_recording()
	result = System.transcribe(audio_segment)
	print("========")
	print(result)
	print("========")
	
	speech = System.speak(result)
	player.play(speech)

# Create a PyQt application and button
app = QApplication([])
button = QPushButton('Hold to record')
button.pressed.connect(on_button_press)
button.released.connect(on_button_release)
button.show()

# Run the PyQt event loop
app.exec_()