import argparse
from PyQt5.QtWidgets import QApplication, QPushButton
from AbstractAI.Helpers.AudioRecorder import AudioRecorder
from AbstractAI.SpeechToText.RemoteSTT import RemoteSTT

def on_button_press():
	recorder.start_recording()

def on_button_release():
	file_name = 'temp.wav'
	
	audio_segment = recorder.stop_recording()
	audio_segment.export(file_name, format="wav")
	result = remote_stt.transcribe_str(file_name)
	
	print(f"Transcribed audio at {recorder.last_record_time/remote_stt.last_transcription_time} Seconds per second. Which returned: '{result}'.")

parser = argparse.ArgumentParser(description='Remote Speech-to-Text Client')
parser.add_argument('host', type=str, help='The server\'s IP address or hostname (e.g., \'localhost\' or \'0.0.0.0\').')
parser.add_argument('port', type=int, help='The port number on which the server is running (e.g., 8000).')
args = parser.parse_args()

recorder = AudioRecorder()
remote_stt = RemoteSTT(args.host, args.port)

app = QApplication([])
button = QPushButton('Hold to record')
button.pressed.connect(on_button_press)
button.released.connect(on_button_release)
button.show()

app.exec_()
