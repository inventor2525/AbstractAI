from AbstractAI.SpeechToText.Transcriber import *
from AbstractAI.SpeechToText.VAD import *
from AbstractAI.Helpers.Signal import *

import threading
from queue import Queue
from typing import Iterator
from dataclasses import dataclass, field

@DATA
@dataclass
class StreamedTranscriptions:
	transcriptions:List[Transcription] = field(default_factory=list)
	# Transcriptions, in the order they were completed
	
	full_audio:Audio = field(default=None)
	# The full, un-clipped or trimmed recorded audio during the time the VAD was active.

@dataclass
class TranscriptionIterator:
	audio_recorder: AudioRecorder
	vad: VAD
	transcriptions: StreamedTranscriptions = field(default=None, init=False)
	
	def __post_init__(self):
		self.transcription_queue = Queue()
		self.stop_event = threading.Event()
		self.transcription_ready = threading.Event()

	def __enter__(self):
		self.transcriptions = StreamedTranscriptions()
		
		self.audio_recorder.start_listening()
		self.audio_recorder.start_recording()
		self._record_start_time = self.audio_recorder.last_peek
		self.vad.start()
		return self

	def __exit__(self, exc_type, exc_val, exc_tb):
		self.stop_event.set()
		self.vad.stop()
		self.transcriptions.full_audio = Audio(
			self.audio_recorder.stop_recording(),
			self._record_start_time
		)
		AppContext.engine.merge(self.transcriptions)
		self.audio_recorder.stop_listening()

	def _on_transcription_completed(self, job: TranscriptionJob, status=JobStatus):
		if status == JobStatus.SUCCESS:
			job.completed.disconnect(self._on_transcription_completed)
			self.transcriptions.transcriptions.append(job.transcription)
			self.transcription_queue.put(job.transcription)
			self.transcription_ready.set()

	def _process_voice_segments(self):
		for audio in self.vad.voice_segments():
			if self.stop_event.is_set():
				break
			transcription_job = TranscriptionJob(
				job_key="Transcribe", audio=audio
			)
			transcription_job.completed.connect(self._on_transcription_completed)
			AppContext.jobs.add(transcription_job)
		#TODO: we never get notification this is done, and hens iterate transcriptions forever, even when not getting voice segments

	def __iter__(self) -> Iterator[Transcription]:
		threading.Thread(target=self._process_voice_segments, daemon=True).start()

		while not self.stop_event.is_set():
			self.transcription_ready.wait(timeout=0.1)
			while not self.transcription_queue.empty():
				yield self.transcription_queue.get()
			self.transcription_ready.clear()