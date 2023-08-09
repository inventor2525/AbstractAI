import sounddevice as sd
import numpy as np
from pydub import AudioSegment
from .Stopwatch import Stopwatch
import threading

class AudioRecorder:
	def __init__(self):
		self.stream = sd.InputStream(samplerate=16000, channels=1, dtype='float32')
		self.recording_thread = self.RecordingThread(self)
		self.buffer = np.array([], dtype='float32')

	class RecordingThread(threading.Thread):
		def __init__(self, recorder):
			super().__init__()
			self.running = False
			self.lock = threading.Lock()
			self.recorder = recorder

		def run(self):
			self.running = True
			print("...........starting thread............")
			self.recorder.stream.start()
			while self.running:
				data, _ = self.recorder.stream.read(1024)
				with self.lock:
					self.recorder.buffer = np.append(self.recorder.buffer, data)
			self.recorder.stream.stop()
			print("...........stopping thread............")

		def stop(self):
			with self.lock:
				self.running = False
			self.recorder.stream.stop()

	def start_recording(self):
		Stopwatch.singleton.start("Recording")
		self.buffer = np.array([], dtype='float32')
		self.recording_thread.start()

	def stop_recording(self):
		self.recording_thread.stop()
		self.last_record_time = Stopwatch.singleton.stop("Recording")["last"]
		audio_data = np.int16(self.buffer * 32767).tobytes()

		Stopwatch.singleton.start("Saving")
		audio_segment = AudioSegment(
			data=audio_data,
			sample_width=2,
			frame_rate=16000,
			channels=1
		)
		Stopwatch.singleton.stop("Saving")
		
		return audio_segment
