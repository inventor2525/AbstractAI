from PyQt5.QtWidgets import QApplication, QPushButton, QVBoxLayout, QWidget, QLabel
from AbstractAI.Helpers.AudioRecorder import *
from AbstractAI.SpeechToText.ChunkedTranscription import ChunkedTranscription
from AbstractAI.SpeechToText.WhisperSTT import WhisperSTT
import json


from PyQt5.QtWidgets import QApplication, QPushButton, QVBoxLayout, QWidget, QLabel
from PyQt5.QtCore import QThread, pyqtSignal
import time

class AudioTranscriptionApp(QWidget):
    def __init__(self, recorder, transcriber):
        super().__init__()
        self.recorder = recorder
        self.transcriber = transcriber
        self.initUI()

    def initUI(self):
        self.button = QPushButton('Hold to record', self)
        self.button.pressed.connect(self.on_button_press)
        self.button.released.connect(self.on_button_release)

        layout = QVBoxLayout(self)
        layout.addWidget(self.button)
        self.setLayout(layout)

    def on_button_press(self):
        self.recorder.start_recording()
        self.transcription_thread = TranscriptionThread(self.recorder, self.transcriber)
        self.transcription_thread.start()

    def on_button_release(self):
        self.transcription_thread.stop()
        remaining_audio = self.recorder.peak()  # Get the remaining audio segment
        self.recorder.stop_recording()  # Dummy stop recording
        if remaining_audio:
            print(self.transcriber.add_audio_segment(remaining_audio))

class TranscriptionThread(QThread):
    def __init__(self, recorder, transcriber):
        super().__init__()
        self.recorder = recorder
        self.transcriber = transcriber
        self.running = False

    def run(self):
        self.running = True
        while self.running:
            time.sleep(1)  # Peak every second
            audio_segment = self.recorder.peak()
            if audio_segment:
                print(self.transcriber.add_audio_segment(audio_segment))

    def stop(self):
        self.running = False
        self.wait()  # Wait for the thread to finish

# Usage
recorder = AudioRecorder()

app = QApplication([])

transcriber = ChunkedTranscription(WhisperSTT("tiny.en"), WhisperSTT("small.en"))
audio_app = AudioTranscriptionApp(recorder, transcriber)
audio_app.show()
app.exec_()
