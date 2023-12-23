import sounddevice as sd
import numpy as np
from pydub import AudioSegment
from .Stopwatch import Stopwatch
import threading

class AudioRecorder:
	def __init__(self):
		devices = sd.query_devices()
		input_device_index = None
		sample_rate = 0
		for i, device in enumerate(devices):
			if device['max_input_channels'] > 0:
				input_device_index = i
				self.sample_rate = device['default_samplerate']
				break
		if input_device_index is None:
			raise ValueError("No input devices found.")
		self.stream = sd.InputStream(samplerate=self.sample_rate, channels=1, dtype='float32', device=input_device_index)
		self.recording_thread = self.RecordingThread(self)
		self.lock = threading.Lock()
		self.recording_thread.start()

	class RecordingThread(threading.Thread):
		def __init__(self, recorder):
			super().__init__(daemon=True)  # Make the thread a daemon thread
			self.record = False
			self.recorder = recorder
			self.temporary_buffer = np.array([], dtype='float32')

		def run(self):
			print("Starting recorder thread.")
			self.recorder.stream.start()
			try:
				while True:
					data, _ = self.recorder.stream.read(1024)
					if self.record:
						self.temporary_buffer = np.append(self.temporary_buffer, data)
					else:
						self.temporary_buffer = data
			except KeyboardInterrupt:
				print("Stopping recorder thread.")
				self.recorder.stream.stop()
				return

	def start_recording(self):
		with self.lock:
			Stopwatch.singleton.start("Recording")
			self.recording_thread.record = True
			self.buffer = np.array([], dtype='float32')

	def stop_recording(self):
		with self.lock:
			self.recording_thread.record = False
			self.buffer = self.recording_thread.temporary_buffer
			self.recording_thread.temporary_buffer = np.array([], dtype='float32')
			self.last_record_time = Stopwatch.singleton.stop("Recording")["last"]
			audio_data = np.int16(self.buffer * 32767).tobytes()

			Stopwatch.singleton.start("Saving")
			audio_segment = AudioSegment(
				data=audio_data,
				sample_width=2,
				frame_rate=int(self.sample_rate),
				channels=1
			)
			Stopwatch.singleton.stop("Saving")

			return audio_segment
