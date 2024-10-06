import sounddevice as sd
import numpy as np
from pydub import AudioSegment
from .Stopwatch import Stopwatch
import threading

class AudioRecorder:
	def __init__(self):
		devices = sd.query_devices()
		input_devices = [(index,device) for index,device in enumerate(devices) if device['max_input_channels'] > 0]
		if len(input_devices) == 0:
			raise ValueError("No input devices found.")
		self.input_device_index, self.device = input_devices[0]
		self.sample_rate = self.device['default_samplerate']
		
		self.recording_thread = self.RecordingThread(self)
		self.lock = threading.Lock()
		self.buffers = [[]]
		self.recording_thread.start()

	class RecordingThread(threading.Thread):
		def __init__(self, recorder:'AudioRecorder'):
			super().__init__(daemon=True)
			self.listen = True
			self.record = False
			self.recorder = recorder
			self.temporary_buffer = np.array([], dtype='float32')

		def run(self):
			print("Starting recorder thread.")
			self.stream = sd.InputStream(
				samplerate=self.recorder.sample_rate,
				channels=1, dtype='float32', 
				device=self.recorder.input_device_index
			)
			self.stream.start()
			try:
				while self.listen:
					data, _ = self.stream.read(1024)
					if self.record:
						with self.recorder.lock:
							self.recorder.buffers[-1].append(data.copy())
					else:
						self.temporary_buffer = data
			except Exception as e:
				print("Stopping recorder thread.")
			self.stream.stop()
			self.stream.close()
			del self.stream
	
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