from AbstractAI.Helpers.AudioRecorder import AudioRecorder
from AbstractAI.Helpers.AudioPlayer import AudioPlayer
from AbstractAI.Model.Settings.TTS_Settings import Hacky_Whisper_Settings
from ClassyFlaskDB.DefaultModel import Object, DATA
from AbstractAI.AppContext import AppContext
from AbstractAI.Helpers.Jobs import Job, Jobs, JobStatus
from pydub import AudioSegment
from dataclasses import dataclass, field
from typing import Optional
import time

@DATA
@dataclass
class Transcription(Object):
    audio_segment: AudioSegment = field(default=None, init=False)
    audio_length: float = field(default=None, init=False)
    transcription: str = field(default=None, init=False)
    transcription_time: float = field(default=None, init=False)
    transcription_rate: float = field(default=None, init=False)
    raw_data: dict = field(default_factory=dict, init=False)

    @classmethod
    def from_AudioSegment(cls, audio_segment:AudioSegment) -> 'Transcription':
        transcription = cls()
        transcription.audio_segment = audio_segment
        transcription.audio_length = audio_segment.duration_seconds
        return transcription
        
    def __str__(self):
        if not self.audio_length:
            return "No recording."
        if not self.transcription_time:
            return f"Un-Transcribed recording, {self.audio_length:.2f}s"
        try:
            return (f"Recording time: {self.audio_length:.2f}s | "
                    f"Transcription time: {self.transcription_time:.2f}s | "
                    f"Transcription rate: {self.transcription_rate:.2f}s/s")
        except Exception as e:
            return (f"Recording time: {self.audio_length}s | "
                    f"Transcription time: {self.transcription_time}s | "
                    f"Transcription rate: {self.transcription_rate}s/s")

@DATA(excluded_fields=["callback", "work", "status_changed", "should_stop", "jobs"])
@dataclass
class TranscriptionJob(Job):
    transcription: Transcription = field(default=None)

class Transcriber:
    def __init__(self, hacky_tts_settings: Hacky_Whisper_Settings, recorder:AudioRecorder=None, player:AudioPlayer=None):
        #TODO: remove recorder and recording indicator from this entirely, put it in the new ApplicationCore
        if recorder:
            self.recorder = recorder
        else:
            self.recorder = AudioRecorder()
        
        if player:
            self.player = player
        else:
            self.player = AudioPlayer()
        
        self.hacky_tts_settings = hacky_tts_settings
        self.is_recording = False
        self.recording_indicator = None
        self.last_transcription:Transcription = None

        if hacky_tts_settings.use_groq:
            self._ensure_groq_loaded()
        else:
            self._ensure_local_model_loaded()

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
        self.is_recording = True

    def stop_recording(self) -> Transcription:
        if self.recording_indicator:
            self.recording_indicator.is_recording = False
        audio_segment = self.recorder.stop_recording()
        self.is_recording = False
        
        transcription = Transcription.from_AudioSegment(audio_segment)
        self.last_transcription = transcription

        return transcription
    
    def _get_audio_path(self, audio:AudioSegment) -> str:
        try:
            return AppContext.engine.get_binary_path(audio)
        except:
            return audio.export("temp_audio.mp3")
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

        return transcription

    def _transcribe_with_groq(self, transcription: Transcription):
        self._ensure_groq_loaded()
        audio_path = self._get_audio_path(transcription.audio_segment)
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
        transcription.raw_data = data
        transcription.transcription = transcription.raw_data['text']

    def _transcribe_with_local_model(self, transcription: Transcription):
        self._ensure_local_model_loaded()
        audio_path = self._get_audio_path(transcription.audio_segment)
        segments, info = self.model.transcribe(audio_path, beam_size=5)
        segments_list = list(segments)

        transcription.raw_data = {
            "segments": [dict(segment._asdict()) for segment in segments_list],
            "info": dict(info._asdict())
        }
        transcription.transcription = " ".join([segment.text for segment in segments_list])

    def play_transcription(self, transcription: Transcription):
        if transcription and transcription.audio_segment:
            self.player.play(transcription.audio_segment)
        else:
            print("No recording to play. Record something first.")
    
    def play_last_recording(self):
        self.play_transcription(self.last_transcription)