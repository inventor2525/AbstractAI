from AbstractAI.Helpers.AudioRecorder import AudioRecorder
from AbstractAI.Helpers.AudioPlayer import AudioPlayer
from AbstractAI.Model.Settings.TTS_Settings import Hacky_Whisper_Settings
from ClassyFlaskDB.DefaultModel import Object, DATA
from ClassyFlaskDB.new.SQLStorageEngine import SQLStorageEngine
from AbstractAI.UI.Context import Context
from AbstractAI.Helpers.Jobs import Jobs, Job
from pydub import AudioSegment
from dataclasses import dataclass, field
from typing import Optional
import time
from datetime import datetime

@DATA
@dataclass
class Transcription(Object):
    audio_segment: AudioSegment = field(default=None, init=False)
    audio_length: float = field(default=None, init=False)
    transcription: str = field(default=None, init=False)
    transcription_time: float = field(default=None, init=False)
    transcription_rate: float = field(default=None, init=False)
    raw_data: dict = field(default_factory=dict, init=False)

    def __str__(self):
        return (f"Recording time: {self.audio_length:.2f}s | "
                f"Transcription time: {self.transcription_time:.2f}s | "
                f"Transcription rate: {self.transcription_rate:.2f}s/s")

class Transcriber:
    def __init__(self, hacky_tts_settings: Hacky_Whisper_Settings):
        self.recorder = AudioRecorder()
        self.player = AudioPlayer()
        self.hacky_tts_settings = hacky_tts_settings
        self.is_recording = False
        self.recording_indicator = None
        self.start_time = None

        if hacky_tts_settings.use_groq:
            self._ensure_groq_loaded()
        else:
            self._ensure_local_model_loaded()

        Jobs.register("transcription", self.work_transcription, self.callback_transcription)

    def _ensure_groq_loaded(self):
        if hasattr(self, "client"):
            return
        from groq import Groq
        try:
            self.client = Groq(api_key=self.hacky_tts_settings.groq_api_key)
        except Exception as e:
            print(f"Error loading groq whisper: {e}")

    def _ensure_local_model_loaded(self):
        if hasattr(self, "model"):
            return
        from faster_whisper import WhisperModel
        try:
            self.model = WhisperModel(
                self.hacky_tts_settings.model_name,
                device=self.hacky_tts_settings.device,
                compute_type=self.hacky_tts_settings.compute_type
            )
        except Exception as e:
            print(f"Error loading local whisper: {e}")

    def toggle_recording(self) -> Optional[Transcription]:
        if self.is_recording:
            return self.stop_recording()
        else:
            self.start_recording()
            return None

    def start_recording(self):
        if self.recording_indicator:
            self.recording_indicator.is_recording = True
        self.recorder.start_recording()
        self.start_time = time.time()
        self.is_recording = True

    def stop_recording(self) -> Transcription:
        if self.recording_indicator:
            self.recording_indicator.is_recording = False
        audio_segment = self.recorder.stop_recording()
        self.is_recording = False

        transcription = Transcription()
        transcription.audio_segment = audio_segment
        transcription.audio_length = time.time() - self.start_time

        Context.engine.merge(transcription)
        
        job = Job(job_key="transcription", name=f"Transcription {transcription.auto_id}")
        Context.jobs.add(job)

        return transcription

    def transcribe(self, transcription: Transcription) -> Transcription:
        if self.recording_indicator:
            self.recording_indicator.is_processing = True

        start_time = time.time()
        try:
            self._transcribe_with_groq(transcription)
        except:
            self._transcribe_with_local_model(transcription)

        transcription.transcription_time = time.time() - start_time
        transcription.transcription_rate = transcription.transcription_time / transcription.audio_length

        if self.recording_indicator:
            self.recording_indicator.is_processing = False

        Context.engine.merge(transcription)
        return transcription

    def _transcribe_with_groq(self, transcription: Transcription):
        self._ensure_groq_loaded()
        audio_data = transcription.audio_segment.export(format="mp3").read()
        result = self.client.audio.transcriptions.create(
            file=("audio.mp3", audio_data),
            model="whisper-large-v3",
            prompt="Specify context or spelling",
            response_format="verbose_json",
            language="en",
            temperature=0.0
        )
        transcription.raw_data = dict(result)
        transcription.transcription = transcription.raw_data['text']

    def _transcribe_with_local_model(self, transcription: Transcription):
        self._ensure_local_model_loaded()
        with transcription.audio_segment.export(format="wav") as audio_file:
            segments, info = self.model.transcribe(audio_file.name, beam_size=5)
            segments_list = list(segments)

        transcription.raw_data = {
            "language": info.language,
            "language_probability": info.language_probability,
            "segments": [
                {
                    "start": segment.start,
                    "end": segment.end,
                    "text": segment.text
                } for segment in segments_list
            ]
        }
        transcription.transcription = " ".join([segment.text for segment in segments_list])

    def play_last_recording(self, transcription: Transcription):
        if transcription and transcription.audio_segment:
            self.player.play(transcription.audio_segment)
        else:
            print("No recording to play. Record something first.")

    def work_transcription(self, job: Job) -> bool:
        transcription = Context.engine.query(Transcription).filter_by_id(job.name.split()[-1])
        if transcription:
            self.transcribe(transcription)
            return True
        return False

    def callback_transcription(self, job: Job):
        transcription = Context.engine.query(Transcription).filter_by_id(job.name.split()[-1])
        if transcription:
            print(f"Transcription completed: {transcription}")