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
		self.buffers = [[]]  # Initialize with an empty list
		self.recording_thread.start()

	class RecordingThread(threading.Thread):
		def __init__(self, recorder):
			super().__init__(daemon=True)
			self.listen = True
			self.record = False
			self.recorder = recorder
			self.temporary_buffer = np.array([], dtype='float32')

		def run(self):
			print("Starting recorder thread.")
			self.recorder.stream.start()
			try:
				while self.listen:
					data, _ = self.recorder.stream.read(1024)
					if self.record:
						with self.recorder.lock:
							self.recorder.buffers[-1].append(data.copy())
					else:
						self.temporary_buffer = data
			except Exception as e:
				print("Stopping recorder thread.")
			self.recorder.stream.stop()
	
	def start_recording(self) -> bool:
		assert self.recording_thread and self.recording_thread.is_alive and self.recording_thread.listen, "Cant record when not listening."
		with self.lock:
			Stopwatch.singleton.start("Recording")
			if self.recording_thread.record:
				return False
			
			self.recording_thread.record = True
			return True

	def stop_recording(self):
		assert self.recording_thread and self.recording_thread.is_alive and self.recording_thread.listen, "Cant stop recording after listening stops."
		with self.lock:
			self.last_record_time = Stopwatch.singleton.stop("Recording")["last"]
			
			if self.buffers:
				self.recording_thread.record = False
				final_buffer = np.concatenate([np.concatenate(buffer) for buffer in self.buffers])
				self.buffers = [[]]  # Reset with a new empty list
				audio_data = np.int16(final_buffer * 32767).tobytes()
				return AudioSegment(
					data=audio_data,
					sample_width=2,
					frame_rate=int(self.sample_rate),
					channels=1
				)
			return AudioSegment.empty()

	def peak(self):
		peak_buffer = None
		assert self.recording_thread and self.recording_thread.is_alive and self.recording_thread.listen, "Cant peak recordings when not listening."
		with self.lock:
			if self.buffers[-1]:
				peak_buffer = np.concatenate(self.buffers[-1])
				self.buffers.append([])  # Add a new empty list for future recording
		
		if peak_buffer is not None:
			audio_data = np.int16(peak_buffer * 32767).tobytes()
			return AudioSegment(
				data=audio_data,
				sample_width=2,
				frame_rate=int(self.sample_rate),
				channels=1
			)
		else:
			return AudioSegment.empty()
	
	def stop_listening(self):
		'''
		There is a background thread that pulls the
		audio stream from the device so it can be
		recorded. This shuts that down before app
		close, and blocks until it's quickly closed.
		'''
		if self.recording_thread and self.recording_thread.is_alive and self.recording_thread.listen:
			print("Stopping recorder...")
			self.recording_thread.listen = False
			self.recording_thread.join()
			print("Recorder terminated!")