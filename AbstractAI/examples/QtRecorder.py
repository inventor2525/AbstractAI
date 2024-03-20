from PyQt5.QtWidgets import QApplication, QPushButton, QVBoxLayout, QWidget
from AbstractAI.Helpers.AudioRecorder import *
from AbstractAI.Helpers.AudioPlayer import *
from datetime import datetime

class RecorderApp(QWidget):
	def __init__(self, recorder: AudioRecorder, player: AudioPlayer):
		super().__init__()
		self.recorder = recorder
		self.player = player
		self.initUI()

	def initUI(self):
		self.record_button = QPushButton('Hold to record', self)
		self.record_button.pressed.connect(self.on_button_press)
		self.record_button.released.connect(self.on_button_release)

		self.play_button = QPushButton('Play last recording', self)
		self.play_button.clicked.connect(self.on_play_button_press)
		
		layout = QVBoxLayout(self)
		layout.addWidget(self.record_button)
		layout.addWidget(self.play_button)
		self.setLayout(layout)

	def on_button_press(self):
		self.recorder.start_recording()

	def on_button_release(self):
		self.prev_segment = self.recorder.stop_recording()
		print(f"Recorded {self.prev_segment.duration_seconds} seconds of audio.")
		
		# Save the audio to a file
		self.prev_segment.export(f"recorded_audio_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.wav", format="wav")
	
	def on_play_button_press(self):
		if self.prev_segment is not None:
			self.player.play(self.prev_segment)
		else:
			print("No recording to play. Record something first.")

# Usage
recorder = AudioRecorder()
player = AudioPlayer()

app = QApplication([])

Stopwatch.singleton.should_log = False
audio_app = RecorderApp(recorder, player)
audio_app.show()
app.exec_()
