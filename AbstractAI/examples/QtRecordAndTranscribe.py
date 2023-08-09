from PyQt5.QtWidgets import QApplication, QPushButton, QVBoxLayout, QWidget, QLabel
from AbstractAI.Helpers.AudioRecorder import *  # Assuming the class is in a file called 'audio_recorder.py'
from AbstractAI.SpeechToText.WhisperSTT import WhisperSTT  # Assuming the class is in a file called 'stt.py'

recorder = AudioRecorder()
stt = WhisperSTT("tiny.en")

def on_button_press():
	recorder.start_recording()

def on_button_release():
	file_name = 'temp.wav'
	
	audio_segment = recorder.stop_recording()
	audio_segment.export(file_name, format="wav")
	result = stt.transcribe_str(file_name)
	
	print(f"Transcribed audio at {recorder.last_record_time/stt.last_transcription_time} Seconds per second. Which returned: '{result}'.")

# Create a PyQt application and button
app = QApplication([])
button = QPushButton('Hold to record')
button.pressed.connect(on_button_press)
button.released.connect(on_button_release)
button.show()

# Run the PyQt event loop
app.exec_()