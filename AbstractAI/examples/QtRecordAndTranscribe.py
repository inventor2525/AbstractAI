from PyQt5.QtWidgets import QApplication, QPushButton, QVBoxLayout, QWidget, QLabel
from AbstractAI.Helpers.AudioRecorder import *
from AbstractAI.SpeechToText.ChunkedTranscription import ChunkedTranscription
from AbstractAI.SpeechToText.WhisperSTT import WhisperSTT
import json


from PyQt5.QtWidgets import QApplication, QPushButton, QVBoxLayout, QWidget, QLabel
from PyQt5.QtCore import QThread, pyqtSignal
from threading import Lock
import time

class AudioTranscriptionApp(QWidget):
    def __init__(self, recorder: AudioRecorder, transcriber: ChunkedTranscription):
        super().__init__()
        self.recorder = recorder
        self.transcriber = transcriber
        self.lock = Lock()
        self.is_recording = False
        self.last_segment = None
        self.transcription_thread = TranscriptionThread(self)
        self.transcription_thread.start()
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
        with self.lock:
            self.is_recording = True

    def on_button_release(self):
        last_segment = self.recorder.peak()
        self.recorder.stop_recording()  # Dummy stop recording
        with self.lock:
            self.is_recording = False
            self.last_segment = last_segment

class TranscriptionThread(QThread):
    def __init__(self, app: AudioTranscriptionApp):
        super().__init__()
        self.app = app

    def run(self):
        last_peak_time = time.time()
        while True:
            time.sleep(max(1 - (time.time() - last_peak_time), 0))
            done = False
            with self.app.lock:
                if self.app.is_recording:
                    audio_segment = self.app.recorder.peak()
                    last_peak_time = time.time()
                else:
                    audio_segment = self.app.last_segment
                    self.app.last_segment = None
                    done = True

            if audio_segment:
                if done:
                    print("Done recording")
                    print(self.app.transcriber.finish_transcription(audio_segment))
                else:
                    print(self.app.transcriber.add_audio_segment(audio_segment))

# Usage
recorder = AudioRecorder()

app = QApplication([])

Stopwatch.singleton.debug = False
transcriber = ChunkedTranscription(WhisperSTT("tiny.en"), WhisperSTT("small.en"))
audio_app = AudioTranscriptionApp(recorder, transcriber)
audio_app.show()
app.exec_()
