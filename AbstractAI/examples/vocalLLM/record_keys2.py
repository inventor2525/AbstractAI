import sys
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtCore import QTimer

from AbstractAI.UI.Support.RecordingIndicator import RecordingIndicator
from AbstractAI.UI.Support.TextTyper import TextTyper
from AbstractAI.UI.Support.KeyComboHandler import KeyComboHandler, KeyAction, KeyEvent
from AbstractAI.UI.Support.TranscriptionWindow import TranscriptionWindow
from AbstractAI.SpeechToText.LiveSpeechToText import LiveSpeechToText

from AbstractAI.Helpers.AudioRecorder import AudioRecorder
from AbstractAI.SpeechToText.ChunkedTranscription import ChunkedTranscription, TranscriptionState
from AbstractAI.SpeechToText.WhisperSTT import WhisperSTT
from AbstractAI.SpeechToText.RemoteSTT import RemoteSTT

class Application():
	def __init__(self, app: QApplication):
		super().__init__()

		self.recordingIndicator = RecordingIndicator() #TODO: handle mouse events
		self.recordingIndicator.show()
		
		self.transcription_window = TranscriptionWindow()
		self.transcription_window.showNearCursor()
		self.transcription_window.hide()
		
		self.textTyper = TextTyper(app)
		
		self.audioRecorder = AudioRecorder()
		self.transcriber = ChunkedTranscription(WhisperSTT("tiny.en"), RemoteSTT())
		self.liveSTT = LiveSpeechToText(self.transcriber, self.audioRecorder, self.on_transcription_occurred)
		
		self.key_handler = KeyComboHandler(key_actions=[
			KeyAction(device_name="ThinkPad Extra Buttons", keycode='KEY_PROG1', key_event_type=KeyEvent.KEY_DOWN, action=self.toggle_recording),
			KeyAction(device_name="AT Translated Set 2 keyboard", keycode='KEY_CALC', key_event_type=KeyEvent.KEY_DOWN, action=self.toggle_recording),
			KeyAction(device_name="Apple, Inc Apple Keyboard", keycode='KEY_F19', key_event_type=KeyEvent.KEY_DOWN, action=self.toggle_recording)
		])
		
		self.prev_transcription = None
		self.should_remove_prev = False
	
	def on_transcription_occurred(self, transcription:TranscriptionState):
		print(transcription)
		
		# self.transcription_window.update_transcription(transcription.fixed_transcription, transcription.living_transcription)
		if self.should_remove_prev:
			self.textTyper.un_type()
			self.should_remove_prev = False
			
		if transcription.length_added > 0:
			self.textTyper.type_str(transcription.peal())
		elif len(transcription.living_transcription) > 0:
			self.textTyper.type_str(transcription.living_transcription)
			self.should_remove_prev = True
	
	def toggle_recording(self):
		if self.liveSTT.is_recording:
			self.liveSTT.stop()
			self.transcription_window.hide()
		else:
			self.liveSTT.start()
			self.transcription_window.showNearCursor()
		self.recordingIndicator.is_recording = self.liveSTT.is_recording

if __name__ == '__main__':
	app = QApplication(sys.argv)
	Application(app)
	sys.exit(app.exec_())