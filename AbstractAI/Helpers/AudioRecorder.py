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
		self.buffers = []
		self.recording_thread.start()

	class RecordingThread(threading.Thread):
		def __init__(self, recorder):
			super().__init__(daemon=True)
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
						with self.recorder.lock:
							if not self.recorder.buffers:
								self.recorder.buffers.append(self.temporary_buffer)
							self.recorder.buffers[-1] = np.append(self.recorder.buffers[-1], data)
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
			self.buffers.append(np.array([], dtype='float32'))

	def stop_recording(self):
		with self.lock:
			self.recording_thread.record = False
			final_buffer = np.concatenate(self.buffers)
			self.buffers = []
			self.last_record_time = Stopwatch.singleton.stop("Recording")["last"]
			audio_data = np.int16(final_buffer * 32767).tobytes()
			return AudioSegment(
				data=audio_data,
				sample_width=2,
				frame_rate=int(self.sample_rate),
				channels=1
			)

	def peak(self):
		with self.lock:
			if self.buffers:
				peak_buffer = self.buffers[-1]
				audio_data = np.int16(peak_buffer * 32767).tobytes()
				return AudioSegment(
					data=audio_data,
					sample_width=2,
					frame_rate=int(self.sample_rate),
					channels=1
				)
			else:
				return None