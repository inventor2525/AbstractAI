from PyQt5.QtWidgets import QApplication, QPushButton, QVBoxLayout, QWidget, QLabel
from AbstractAI.Helpers.AudioRecorder import *
from AbstractAI.SpeechToText.WhisperSTT import WhisperSTT
import json

recorder = AudioRecorder()
stt = WhisperSTT("small.en")

def on_button_press():
	recorder.start_recording()

def on_button_release():
	audio_segment = recorder.stop_recording()
	result = stt.transcribe(audio_segment)
	print(f"Transcribed audio at {recorder.last_record_time/stt.last_transcription_time} Seconds per second. Which returned: '{result['text']}'.")
	print("========")
	print(json.dumps(result, indent=4))
	print("========")

# Create a PyQt application and button
app = QApplication([])
button = QPushButton('Hold to record')
button.pressed.connect(on_button_press)
button.released.connect(on_button_release)
button.show()

# Run the PyQt event loop
app.exec_()