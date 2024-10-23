import sounddevice as sd
import numpy as np
from pydub import AudioSegment
from .Stopwatch import Stopwatch
from typing import TypeVar, Type
import threading

T = TypeVar("T")
class AudioRecorder:
	def __init__(self):
		#Locate the first audio recording device:
		devices = sd.query_devices()
		input_devices = [(index,device) for index,device in enumerate(devices) if device['max_input_channels'] > 0]
		if len(input_devices) > 0:
			self.input_device_index, self.device = input_devices[0]
			self.sample_rate = self.device['default_samplerate']
		else:
			self.device = None
		
		#Prep for recording:
		self.recording_thread:AudioRecorder.RecordingThread = None
		self.lock = threading.Lock()
		self.buffers = [[]]
		self.start_listening()
	
	@property
	def is_listening(self) -> bool:
		'''
		Tells you if we're currently streaming audio from device.
		
		(Doesn't tell you if we're recording, though we
		aren't if this is false.)
		'''
		rt = self.recording_thread
		return rt and rt.is_alive and rt.should_listen
	
	def start_listening(self) -> None:
		'''
		Starts listening (if we weren't already). This doesn't
		record, it just gets the stream going.
		
		Be sure to stop it before app close.
		'''
		if self.device and not self.is_listening:
			rt = AudioRecorder.RecordingThread(self)
			self.recording_thread = rt
			rt.start()
		
	class RecordingThread(threading.Thread):
		def __init__(self, recorder:'AudioRecorder'):
			super().__init__(daemon=True)
			self.should_listen = True
			self.should_record = False
			self.recorder = recorder

		def run(self):
			self.stream = sd.InputStream(
				samplerate=self.recorder.sample_rate,
				channels=1, dtype='float32', 
				device=self.recorder.input_device_index
			)
			self.stream.start()
			try:
				was_recording = self.should_record
				prev_buffer = None
				while self.should_listen:
					data, _ = self.stream.read(1024)
					record = self.should_record
					if record:
						with self.recorder.lock:
							if not was_recording and prev_buffer is not None:
								self.recorder.buffers[-1].append(prev_buffer)
							self.recorder.buffers[-1].append(data.copy())
					else:
						prev_buffer = data.copy()
					was_recording = record
			except Exception as e:
				print(f"Stopping recorder thread due to exception: {e}.")
			self.stream.stop()
			self.stream.close()
			del self.stream
	
	def start_recording(self) -> bool:
		'''
		Starts a single new recording, only call this if it's
		listening first (it starts automatically on init).
		'''
		if not self.is_listening:
			print("Cant record when not listening.")
			return False
		
		if self.recording_thread.should_record:
			return True
		
		with self.lock:
			Stopwatch.singleton.start("Recording")
			self.recording_thread.should_record = True
			return True

	def stop_recording(self, return_type:Type[T]=AudioSegment) -> T:
		'''
		Stop recording and return the full recording since you started.
		(Including any times you peeked)
		'''
		assert return_type is AudioSegment or return_type is np.ndarray, "Return type can only be an AudioSegment or np.ndarray"
		
		# Make sure we were recording:
		assert self.is_listening, "Cant stop recording after listening stops."
		assert self.recording_thread.should_record, "Cant stop recording when we never started!"
		
		# Grab the audio we've recorded:
		final_buffer = None
		with self.lock:
			self.last_record_time = Stopwatch.singleton.stop("Recording")["last"]
			
			if self.buffers:
				self.recording_thread.should_record = False
				peek_buffers = []
				for peek_buffer in self.buffers:
					if isinstance(peek_buffer, list):
						peek_buffers.append(np.concatenate(peek_buffer))
					else:
						peek_buffers.append(peek_buffer)
				final_buffer = np.concatenate(peek_buffers)
				self.buffers = [[]]  # Reset with a new empty list
		
		# Format and return the audio:
		if final_buffer is not None:
			if return_type is AudioSegment:
				return self.np_to_AudioSegment(final_buffer)
			return final_buffer
		if return_type is AudioSegment:
			return AudioSegment.empty()
		return np.array([], dtype=np.float32)

	def peek(self, return_type:Type[T]=AudioSegment) -> T:
		'''
		Use this while recording to peek at what we've recorded
		so far, since the time you started recording or since the
		time you last peeked.
		'''
		assert return_type is AudioSegment or return_type is np.ndarray, "Return type can only be an AudioSegment or np.ndarray"
		
		# Make sure we were recording:
		assert self.is_listening, "Cant peek recordings when not listening."
		assert self.recording_thread.should_record, "Cant peek a recording we never started!"
		
		# Add an empty buffer to continue recording
		# with so we can peek into the current one safely:
		peek_buffer = None
		buffer_index = None
		with self.lock:
			if self.buffers[-1]:
				peek_buffer = self.buffers[-1]
				buffer_index = len(self.buffers)-1
				self.buffers.append([])  # Add a new empty list for future recording
		
		# Concatenate the audio data we've recorded since the last peek:
		if peek_buffer is not None:
			peek_buffer = np.concatenate(peek_buffer)
			
			# Save the concatenated version to reduce work when we stop recording:
			with self.lock:
				self.buffers[buffer_index] = peek_buffer
		
		# Format and return the audio:
		if peek_buffer is not None:
			if return_type is AudioSegment:
				return self.np_to_AudioSegment(peek_buffer)
			return peek_buffer
		if return_type is AudioSegment:
			return AudioSegment.empty()
		return np.array([], dtype=np.float32)
	
	def stop_listening(self) -> None:
		'''
		There is a background thread that pulls the
		audio stream from the device so it can be
		recorded. This shuts that down before app
		close, and blocks until it's quickly closed.
		'''
		rt = self.recording_thread
		if rt and rt.is_alive and rt.should_listen:
			print("Stopping recorder...")
			rt.should_listen = False
			rt.join()
			print("Recorder terminated!")
	
	def np_to_AudioSegment(self, array:np.ndarray) -> AudioSegment:
		audio_data = np.int16(array * 32767).tobytes()
		return AudioSegment(
			data=audio_data,
			sample_width=2,
			frame_rate=int(self.sample_rate),
			channels=1
		)