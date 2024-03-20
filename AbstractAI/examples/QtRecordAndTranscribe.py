from PyQt5.QtWidgets import QApplication, QPushButton, QVBoxLayout, QWidget
from AbstractAI.Helpers.AudioRecorder import *
from AbstractAI.SpeechToText.ChunkedTranscription import ChunkedTranscription, TranscriptionState
from AbstractAI.SpeechToText.LiveSpeechToText import LiveSpeechToText
from AbstractAI.SpeechToText.WhisperSTT import WhisperSTT

class AudioTranscriptionApp(QWidget):
    def __init__(self, recorder: AudioRecorder, transcriber: ChunkedTranscription):
        super().__init__()
        self.recorder = recorder
        self.transcriber = transcriber
        self.live_stt = LiveSpeechToText(transcriber, recorder, lambda transcription, self=self: self.on_transcription_occured(transcription))
        self.initUI()

    def initUI(self):
        self.button = QPushButton('Hold to record', self)
        self.button.pressed.connect(self.on_button_press)
        self.button.released.connect(self.on_button_release)

        layout = QVBoxLayout(self)
        layout.addWidget(self.button)
        self.setLayout(layout)

    def on_button_press(self):
        self.live_stt.start()

    def on_button_release(self):
        self.live_stt.stop()
    
    def on_transcription_occured(self, transcription:TranscriptionState):
        print(transcription)
        
# Usage
recorder = AudioRecorder()

app = QApplication([])

Stopwatch.singleton.should_log = False
transcriber = ChunkedTranscription(WhisperSTT("tiny.en"), WhisperSTT("small.en"))
audio_app = AudioTranscriptionApp(recorder, transcriber)
audio_app.show()
app.exec_()
