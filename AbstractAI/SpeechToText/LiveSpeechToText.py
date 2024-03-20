from typing import Callable
from AbstractAI.Helpers.AudioRecorder import *
from AbstractAI.SpeechToText.ChunkedTranscription import ChunkedTranscription, TranscriptionState

from threading import Lock, Thread
import time

from AbstractAI.SpeechToText.Logging.Logger import stt_logger

class LiveSpeechToText:
	class TranscriptionThread(Thread):
		def __init__(self, app: "LiveSpeechToText"):
			super().__init__()
			self.app = app

		def run(self):
			last_peak_time = time.time()
			was_recording = False
			while True:
				time.sleep(max(1 - (time.time() - last_peak_time), 0))
				
				audio_segment = None
				transcription = None
				with self.app.lock:
					if self.app._is_recording:
						was_recording = True
						audio_segment = self.app.recorder.peak()
						stt_logger.end_segment("peak", audio_segment=audio_segment)
						stt_logger.start_segment("peak", "full")
						last_peak_time = time.time()
					elif was_recording:
						transcription = self.app.transcriber.finish_transcription(self.app.last_segment)
						
						self.app.last_segment = None
						was_recording = False
				
				if audio_segment:
					transcription = self.app.transcriber.add_audio_segment(audio_segment)
						
				if transcription:
					self.app.transcription_callback(transcription)
						
	def __init__(self, transcriber:ChunkedTranscription, recorder:AudioRecorder, transcription_callback:Callable[[TranscriptionState], None]):
		self.transcriber = transcriber
		self.recorder = recorder
		self.transcription_callback = transcription_callback
		
		self._is_recording = False
		self.last_segment : AudioSegment = None
		self.transcription_thread = LiveSpeechToText.TranscriptionThread(self)
		self.transcription_thread.start()
		self.lock = Lock()
	
	def start(self) -> bool:
		self.recorder.start_recording()
		with self.lock:
			if self._is_recording:
				return False
			self._is_recording = True
			stt_logger.start_segment("full")
			stt_logger.start_segment("peak", "full")
			return True
	
	def stop(self):
		with self.lock:
			last_segment = self.recorder.peak()
			stt_logger.end_segment("peak", last_segment)
			
			full_recording = self.recorder.stop_recording()
			stt_logger.end_segment("full", full_recording)
			
			self._is_recording = False
			self.last_segment = last_segment
	
	@property
	def is_recording(self):
		with self.lock:
			return self._is_recording