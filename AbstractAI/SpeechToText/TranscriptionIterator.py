from AbstractAI.SpeechToText.Transcriber import *
from AbstractAI.SpeechToText.VAD import *
from AbstractAI.Helpers.Signal import *

import threading
from queue import Queue
from typing import Iterator
from dataclasses import dataclass

@dataclass
class TranscriptionIterator:
	audio_recorder: AudioRecorder
	vad: VAD
	transcription_completed: Signal[[Transcription],None]

	def __post_init__(self):
		self.transcription_queue = Queue()
		self.stop_event = threading.Event()
		self.transcription_ready = threading.Event()

	def __enter__(self):
		self.audio_recorder.start_listening()
		self.audio_recorder.start_recording()
		self.vad.start()
		self.transcription_completed.connect(self._on_transcription_completed)
		return self

	def __exit__(self, exc_type, exc_val, exc_tb):
		self.stop_event.set()
		self.vad.stop()
		all_audio = self.audio_recorder.stop_recording()
		self.audio_recorder.stop_listening()
		self.transcription_completed.disconnect(self._on_transcription_completed)

	def _on_transcription_completed(self, transcription: Transcription):
		self.transcription_queue.put(transcription)
		self.transcription_ready.set()

	def _process_voice_segments(self):
		for audio_segment in self.vad.voice_segments():
			if self.stop_event.is_set():
				break
			AppContext.jobs.add(TranscriptionJob(
				job_key="Transcribe", transcription=Transcription.from_AudioSegment(audio_segment)
			))

	def __iter__(self) -> Iterator[Transcription]:
		threading.Thread(target=self._process_voice_segments, daemon=True).start()

		while not self.stop_event.is_set():
			self.transcription_ready.wait(timeout=0.1)
			while not self.transcription_queue.empty():
				yield self.transcription_queue.get()
			self.transcription_ready.clear()