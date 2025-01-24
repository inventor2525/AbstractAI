from AbstractAI.Helpers.AudioRecorder import AudioRecorder
from AbstractAI.Helpers.AudioPlayer import AudioPlayer
from AbstractAI.Model.Settings.TTS_Settings import TTS_Settings_v1
from AbstractAI.Model.Transcription import *
from AbstractAI.AppContext import AppContext
from AbstractAI.Helpers.Jobs import Job, Jobs, JobStatus
from pydub import AudioSegment
from dataclasses import dataclass, field
from typing import Optional
import time

@DATA
@dataclass
class TranscriptionJob(Job):
	audio: Audio = field(default=None)
	transcription: Transcription = field(default=None)

class Transcriber:
	def __init__(self, tts_settings: TTS_Settings_v1):
		self.tts_settings = tts_settings

		if tts_settings.use_groq:
			self._ensure_groq_loaded()
		elif tts_settings.enable_local_fallback:
			self._ensure_local_model_loaded()
		else:
			raise ValueError("No model enabled in passed settings, groq or local.")
	
	def transcribe(self, audio: Audio) -> Transcription:
		start_time = time.time()
		if self.tts_settings.use_groq:
			transcription = self._transcribe_with_groq(audio)
		else:
			transcription = self._transcribe_with_local_model(audio)

		transcription.transcription_time = time.time() - start_time

		return transcription
	
	def _ensure_groq_loaded(self):
		if hasattr(self, "client"):
			return
		from groq import Groq
		try:
			self.client = Groq(api_key=self.tts_settings.groq_api_key)
		except Exception as e:
			print(f"Error loading groq whisper: {e}")

	def _ensure_local_model_loaded(self):
		if hasattr(self, "model"):
			return
		if not self.tts_settings.enable_local_fallback:
			ValueError("Local model requested but disabled in settings")
		
		from faster_whisper import WhisperModel
		try:
			self.model = WhisperModel(
				self.tts_settings.local_model_name,
				device=self.tts_settings.local_device,
				compute_type=self.tts_settings.local_compute_type
			)
		except Exception as e:
			print(f"Error loading local whisper: {e}")

	def _get_audio_path(self, audio:AudioSegment) -> str:
		try:
			return AppContext.engine.get_binary_path(audio)
		except:
			return audio.export("temp_audio.mp3")

	def _transcribe_with_groq(self, audio: Audio) -> Transcription:
		self._ensure_groq_loaded()
		audio_path = self._get_audio_path(audio.segment)
		data = None
		with open(audio_path, "rb") as audio_file:
			result = self.client.audio.transcriptions.create(
				file=(audio_path, audio_file.read()),
				model="whisper-large-v3",
				prompt="Specify context or spelling",
				response_format="verbose_json",
				language="en",
				temperature=0.0
			)
			data = result.to_dict()
		return Transcription(
			data['text'],
			audio=audio,
			raw_data=data
		)

	def _transcribe_with_local_model(self, audio: Audio) -> Transcription:
		self._ensure_local_model_loaded()
		audio_path = self._get_audio_path(audio.segment)
		segments, info = self.model.transcribe(audio_path, beam_size=5)
		segments_list = list(segments)

		raw_data = {
			"segments": [dict(segment._asdict()) for segment in segments_list],
			"info": dict(info._asdict())
		}
		transcription = " ".join([segment.text for segment in segments_list])
		return Transcription(transcription, audio=audio, raw_data=raw_data)