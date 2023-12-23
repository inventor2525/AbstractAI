from AbstractAI.SpeechToText.WhisperSTT import WhisperSTT

from dataclasses import dataclass
from pydub import AudioSegment
import random

@dataclass
class TranscriptionState:
    fixed_transcription: str = ""
    living_transcription: str = ""
    length_added: int = 0

    def get_total_transcription(self):
        return self.fixed_transcription + self.living_transcription

class ChunkedTranscription:
    def __init__(self, tiny_model: WhisperSTT, large_model: WhisperSTT, consensus_threshold_seconds: int = 10):
        self.tiny_model = tiny_model
        self.large_model = large_model
        self.fixed_transcription = ""
        self.living_audio = AudioSegment.empty()
        self.previous_consensus_time = 0
        self.start_time = 0
        self.consensus_threshold = consensus_threshold_seconds * 1000  # Convert to milliseconds

    def start_transcription(self):
        self.fixed_transcription = ""
        self.living_audio = AudioSegment.empty()
        self.previous_consensus_time = 0
        self.start_time = 0

    def add_audio_segment(self, audio_segment: AudioSegment) -> TranscriptionState:
        self.living_audio += audio_segment

        if len(self.living_audio) > self.consensus_threshold:
            self.start_time = random.randint(0, self.previous_consensus_time // 2)
            self.living_audio = self.living_audio[self.start_time:]

        # Transcribe using the tiny model
        result_tiny = self.tiny_model.transcribe(self.living_audio)

        if self._reached_consensus(result_tiny['segments']):
            consensus_time = self._get_consensus_time(result_tiny['segments'])
            self.previous_consensus_time = consensus_time

            # Transcribe the accumulated living audio using the large model
            result_large = self.large_model.transcribe(self.living_audio)

            # Update fixed transcription
            prev_length = len(self.fixed_transcription)
            self.fixed_transcription += result_large['text']
            length_added = len(self.fixed_transcription) - prev_length

            self.living_audio = self.living_audio[consensus_time:]

            return TranscriptionState(fixed_transcription=self.fixed_transcription, 
                                      living_transcription="", 
                                      length_added=length_added)
        else:
            return TranscriptionState(fixed_transcription=self.fixed_transcription, 
                                      living_transcription=result_tiny['text'], 
                                      length_added=0)

    def _reached_consensus(self, segments) -> bool:
        if len(segments) < 2:
            return False

        _, last_segment_end = self._get_segment_time(segments[-2])
        next_segment_start, _ = self._get_segment_time(segments[-1])
        return (next_segment_start - last_segment_end) >= self.consensus_threshold

    def _get_consensus_time(self, segments) -> int:
        _, last_segment_end = self._get_segment_time(segments[-2])
        next_segment_start, _ = self._get_segment_time(segments[-1])
        consensus_time = (last_segment_end + next_segment_start) // 2
        return min(consensus_time, self.consensus_threshold)

    def _get_segment_time(self, segment) -> (int, int):
        # Adjust the start and end times by the start time
        start = segment['start'] + self.start_time
        end = segment['end'] + self.start_time
        return start, end

# Usage example
tiny_model = WhisperSTT("tiny.en")
large_model = WhisperSTT("small.en")

transcriber = ChunkedTranscription(tiny_model, large_model)
transcriber.start_transcription()
state = transcriber.add_audio_segment(AudioSegment.empty())  # Replace with actual audio segments
