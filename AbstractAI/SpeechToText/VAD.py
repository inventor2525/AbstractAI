import threading
import time
import numpy as np
from AbstractAI.Helpers.Stopwatch import Stopwatch

# Timing some really slow Voice Activity Detection imports:
Stopwatch.singleton("VAD Imports")
Stopwatch.singleton.new_scope()

Stopwatch.singleton("torch")
import torch

Stopwatch.singleton("Model")
from pyannote.audio import Model

Stopwatch.singleton("VoiceActivityDetector")
from pyannote.audio.pipelines import VoiceActivityDetection
Stopwatch.singleton.end_scope()

from AbstractAI.Helpers.AudioRecorder import AudioRecorder
from typing import List, Iterator
from AbstractAI.Model.Audio import Audio, AudioSegment
from ClassyFlaskDB.DefaultModel import *

@DATA
@dataclass
class VADSettings(Object):
	use_remote_model:bool = True
	path:str = "pyannote/segmentation-3.0"
	user_auth_token:str = ""
	min_duration_on:float = 0.0
	min_duration_off:float = 0.0

class VAD:
	'''
	Voice Activity Detector.
	Start after starting a recording with recorder,
	then iterate voice_segments.
	'''
	class Pause:
		'''Pauses the vad when used in a with block.'''
		def __init__(self, vad:'VAD'):
			self.vad = vad
		
		def __enter__(self):
			self.vad.paused = True
			return self
		
		def __exit__(self, exc_type, exc_val, exc_tb):
			self.vad.recorder.peek() # Ensure no audio leaks in from before we un-paused.
			self.vad.paused = False
	
	@dataclass
	class _Segment:
		data:np.ndarray
		start_time:datetime
		end_time:datetime
	
	def __init__(self, settings:VADSettings, recorder: AudioRecorder, peek_interval: float = 0.5, window_padding: float = 1.0):
		"""
		Initialize the Voice Activity Detector.

		Args:
			recorder (AudioRecorder): The audio recorder to use for capturing audio.
			peek_interval (float): The interval in seconds between each audio peek.
			window_padding (float): The padding in seconds to include before and after voice activity.
		"""
		self.settings = settings
		self.recorder = recorder
		self.peek_interval = peek_interval
		self.window_padding = window_padding
		
		# Prep for VAD:
		self.paused = False
		self.running = False
		self.vad_thread: threading.Thread = None
		self.segment_available = threading.Event()
		self.segment_lock = threading.Lock()
		
		self.silent_peeks_buffer: List[VAD._Segment] = []
		self.vocal_segments: List[VAD._Segment] = []

		# Initialize the model
		self.model = Model.from_pretrained(
			settings.path, 
			use_auth_token=settings.user_auth_token if settings.use_remote_model else None)

		# Initialize the pipeline
		self.pipeline = VoiceActivityDetection(segmentation=self.model)
		HYPER_PARAMETERS = {
			"min_duration_on": settings.min_duration_on,
			"min_duration_off": settings.min_duration_off
		}
		self.pipeline.instantiate(HYPER_PARAMETERS)

	def start(self, ignore_prev_audio:bool=False) -> None:
		"""Start the voice activity detection loop."""
		if not self.running:
			self.running = True
			if ignore_prev_audio:
				self.recorder.peek()
			self.vad_thread = threading.Thread(target=self._vad_loop)
			self.vad_thread.start()

	def stop(self) -> None:
		"""Stop the voice activity detection loop."""
		if self.running:
			self.running = False
			self.vad_thread.join()
			self.segment_available.set()  # Ensure the iterator exits if waiting
	
	def _audio_segment_duration(self, segment:np.ndarray) -> float:
		'''Calculates how long this audio segment is (in seconds).'''
		return len(segment) / float(self.recorder.sample_rate)
	
	def _vad_loop(self) -> None:
		"""Main loop for voice activity detection."""
		silent_duration = 0.0
		voice_detected = False
		voice_detected_segments: List[VAD._Segment] = []
		def concat(segs:List[VAD._Segment]) -> VAD._Segment:
			if segs is None or len(segs)==0:
				return None
			return VAD._Segment(
				np.concatenate([b.data for b in segs]),
				segs[0].start_time,
				segs[-1].end_time
			)
		while self.running:
			time.sleep(self.peek_interval)
			peek_data = VAD._Segment(
				self.recorder.peek(return_type=np.ndarray),
				self.recorder.last_peek,
				datetime.now()
			)
			if peek_data.data.size == 0:
				continue
			
			if self.paused:
				self.silent_peeks_buffer.clear()
				voice_detected_segments.clear()
				voice_detected = False
				continue
			
			# Get a longer segment we can check for voice activity more robustly:
			if not voice_detected:
				# If no voice has been detected lately, we'll use
				# the sum of the current peeked audio and all 'silent'
				# buffers we have before hand to make sure they were
				# truly silent when combined with more recent data:
				if len(self.silent_peeks_buffer) > 0:
					segment_data = concat(self.silent_peeks_buffer + [peek_data]).data
				else:
					segment_data = peek_data.data
			else:
				# Else we'll use the last so many segments, up to window_padding seconds ago:
				segments_duration = self._audio_segment_duration(peek_data.data)
				if segments_duration > self.window_padding:
					segment_data = peek_data.data
				else:
					segments = [peek_data]
					for segment in reversed(voice_detected_segments):
						# Accumulate segments off the end of voice_detected_segments
						# until we have > self.window_padding seconds of audio:
						segments_duration += self._audio_segment_duration(segment.data)
						segments.insert(0, segment)
						if segments_duration > self.window_padding:
							break
					segment_data = concat(segments).data
			
			# Check segment for vocal activity:
			segment_duration = self._audio_segment_duration(segment_data)
			segment_vad_result = self._check_voice_activity(segment_data)
			
			if not voice_detected and len(segment_vad_result):
				# If we haven't been detecting a voice but are now:
				voice_detected = True
				
				# Pull in > self.window_padding seconds worth of audio
				# data we have cached from when there was no voice detected:
				first_voice_time = list(segment_vad_result.get_timeline())[0].start
				required_padding = max(0, self.window_padding - first_voice_time)
				self._trim_buffer_queue(required_padding)
				voice_detected_segments = self.silent_peeks_buffer + [peek_data]
				self.silent_peeks_buffer.clear()
				
				# Calculate how long there hasn't been a voice detected so far:
				silent_duration = segment_duration - list(segment_vad_result.get_timeline())[-1].end
			
			elif voice_detected:
				# If we have been detecting a voice:
				voice_detected_segments.append(peek_data)
				if len(segment_vad_result):
					# And still are:
					silent_duration = segment_duration - list(segment_vad_result.get_timeline())[-1].end
				else:
					# But if we are no longer detecting voice:
					silent_duration += self._audio_segment_duration(peek_data.data)
					
				if silent_duration >= self.window_padding:
					# Then if we haven't been detecting voice long enough:
					full_segment = concat(voice_detected_segments)
					total_duration = self._audio_segment_duration(full_segment.data)
					total_vad_result = self._check_voice_activity(full_segment.data)
					
					# Make sure we actually did have a voice
					# and it ended long enough ago:
					if len(total_vad_result) > 0:
						silent_duration = total_duration - list(total_vad_result.get_timeline())[-1].end
						
						if silent_duration >= self.window_padding:
							# If it's been long enough without a voice,
							# queue this recording to be returned:
							with self.segment_lock:
								self.vocal_segments.append(full_segment)
							voice_detected_segments.clear()
							self.segment_available.set()  # Signal that a new vocal segment is available
						# else: Continue recording until the end padding requirement is met
					else:
						# If we didn't in all that we've recorded so far, something
						# went wrong, delete it, and go back to waiting for voice:
						voice_detected = False
						self.silent_peeks_buffer.extend(voice_detected_segments)
						voice_detected_segments.clear()
						
						# Keep some of the silent peeked buffers for latter VAD:
						self._trim_buffer_queue(self.window_padding)
			else:
				# No voice detected, just keep a rolling buffer
				# to make up our padding for once there is some:
				self.silent_peeks_buffer.append(peek_data)
				self._trim_buffer_queue(self.window_padding)
		
		# Finish up by queue'ing any audio we have
		# been building out atm with voice in it:
		if voice_detected:
			last_audio = concat(voice_detected_segments)
			if last_audio is None:
				return
			
			# Make sure it's actually got some voice in it:
			if last_audio.data.size>0 and len(self._check_voice_activity(last_audio.data)) > 0:
				with self.segment_lock:
					# It does, queue it up:
					self.vocal_segments.append(last_audio)

	def _check_voice_activity(self, audio_data: np.ndarray) -> VoiceActivityDetection:
		"""
		Check for voice activity in the given audio data.

		Args:
			audio_data (np.ndarray): The audio data to check.

		Returns:
			VoiceActivityDetection: The result of the voice activity detection.
		"""
		waveform = torch.from_numpy(audio_data).float().t()
		return self.pipeline({'waveform': waveform, 'sample_rate': self.recorder.sample_rate})

	def _trim_buffer_queue(self, required_duration: float) -> None:
		"""
		Trim the silent_peeks_buffer queue to maintain only the required duration of audio.

		Args:
			required_duration (float): The required duration of audio to keep in the buffer.
		"""
		current_duration = 0.0
		for i, buffer in enumerate(reversed(self.silent_peeks_buffer)):
			buffer_duration = self._audio_segment_duration(buffer.data)
			current_duration += buffer_duration
			if current_duration >= required_duration:
				self.silent_peeks_buffer = self.silent_peeks_buffer[-(i+1):]
				break

	def voice_segments(self) -> Iterator[Audio]:
		"""
		Iterates AudioSegments containing voice as they become available.

		Yields:
			AudioSegment: An AudioSegment containing the audio data of a voice.
		"""
		while self.running:
			self.segment_available.wait()  # Wait for a segment to become available
			with self.segment_lock:
				if self.vocal_segments:
					segment = self.vocal_segments.pop(0)
					if not self.vocal_segments:
						self.segment_available.clear()  # Clear the event if no more segments
					yield Audio(
						self.recorder.np_to_AudioSegment(segment.data),
						start_time=segment.start_time,
						date_created=segment.end_time
					)
	
	def pauser(self) -> 'VAD.Pause':
		'''
		Returns a 'Pause' object that can be used with
		'with' syntax to block speech input for a time
		'''
		return VAD.Pause(self)