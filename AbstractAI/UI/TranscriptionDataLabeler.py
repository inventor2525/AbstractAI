import sys
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QTextEdit, QLabel
from PyQt5.QtCore import Qt

from AbstractAI.Helpers.AudioPlayer import AudioPlayer

class TranscriptionDataLabeler(QWidget):
    def __init__(self):
        super().__init__()

        # Layouts
        main_layout = QVBoxLayout()
        top_control_bar = QHBoxLayout()
        playback_control_bar = QHBoxLayout()
        transcription_area = QVBoxLayout()

        # Top Control Bar
        self.prev_recording_button = QPushButton("Prev Recording")
        self.prev_clip_button = QPushButton("Prev Clip")
        self.recording_length_label = QLabel("Length of Full Recording: {}")
        self.number_of_clips_label = QLabel("Number of Clips: {}")
        self.next_clip_button = QPushButton("Next Clip")
        self.next_recording_button = QPushButton("Next Recording")

        top_control_bar.addWidget(self.prev_recording_button)
        top_control_bar.addWidget(self.prev_clip_button)
        top_control_bar.addWidget(self.recording_length_label)
        top_control_bar.addWidget(self.number_of_clips_label)
        top_control_bar.addWidget(self.next_clip_button)
        top_control_bar.addWidget(self.next_recording_button)

        # Playback Control Bar
        self.play_button = QPushButton("Play")
        self.pause_button = QPushButton("Pause")
        self.rewind_10_sec_button = QPushButton("Rewind 10 Sec")
        self.rewind_all_button = QPushButton("Rewind All")

        playback_control_bar.addWidget(self.play_button)
        playback_control_bar.addWidget(self.pause_button)
        playback_control_bar.addWidget(self.rewind_10_sec_button)
        playback_control_bar.addWidget(self.rewind_all_button)

        # Transcription Area
        self.clip_transcription_field = QTextEdit()
        self.full_transcription_field = QTextEdit()
        self.confirm_edit_button = QPushButton("Confirm Edit")

        transcription_area.addWidget(QLabel("Clip Transcription"))
        transcription_area.addWidget(self.clip_transcription_field)
        transcription_area.addWidget(QLabel("Full Transcription"))
        transcription_area.addWidget(self.full_transcription_field)
        transcription_area.addWidget(self.confirm_edit_button)

        # Main Layout
        main_layout.addLayout(top_control_bar)
        main_layout.addLayout(playback_control_bar)
        main_layout.addLayout(transcription_area)

        self.setLayout(main_layout)
        self.setWindowTitle("Data Labeling Tool")
    

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TranscriptionDataLabeler()
    window.show()
    sys.exit(app.exec_())
