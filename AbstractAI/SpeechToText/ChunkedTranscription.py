import json
from AbstractAI.SpeechToText.SpeechToText import SpeechToText
from AbstractAI.Helpers.RangeHeatMap import RangeHeatMap

from dataclasses import dataclass
from pydub import AudioSegment
import random

from dataclasses import dataclass

@dataclass
class TranscriptionState:
	fixed_transcription: str = ""
	living_transcription: str = ""
	length_added: int = 0

	def get_total_transcription(self):
		return self.fixed_transcription + self.living_transcription

class ChunkedTranscription:
	def __init__(self, tiny_model: SpeechToText, large_model: SpeechToText, consensus_threshold_seconds: float = 2, concensus_transcription_threshold: int = 3):
		self.tiny_model = tiny_model
		self.large_model = large_model
		self.consensus_threshold = consensus_threshold_seconds
		self.concensus_transcription_threshold = concensus_transcription_threshold
		self.new_transcription()

	def new_transcription(self):
		self.fixed_transcription = ""
		self.living_audio = AudioSegment.empty()
		self.heat_map = RangeHeatMap()
		self.previous_consensus_time = 0
		self._run_count_since_clipped = 0
		self.start_time = 0
	
	def _clip(self, consensus_time: float, other:str):
		# trans_name = self.fixed_transcription.replace(" ", "_").replace(".", "").replace(",", "")
		# self.living_audio.export(f"living_audio_{trans_name}_{other}_pre_cut.wav", format="wav")
		self.living_audio = self.living_audio[(self.living_audio.duration_seconds-consensus_time)*1000:]
		# self.living_audio.export(f"living_audio_{trans_name}_{other}_post_cut.wav", format="wav")
		self._run_count_since_clipped = 0
		
	def add_audio_segment(self, audio_segment: AudioSegment) -> TranscriptionState:
		self.living_audio += audio_segment
		
		if len(self.living_audio) > self.consensus_threshold:
			self.start_time = random.random() * self.previous_consensus_time / 2
			self.living_audio = self.living_audio[self.start_time:]
		
		# Transcribe using the tiny model
		result_tiny = self.tiny_model.transcribe(self.living_audio)
		self._run_count_since_clipped += 1
		
		# Initialize RangeHeatMap
		# print(json.dumps(result_tiny, indent=4))
		# print(self.heat_map.ranges)
		for segment in result_tiny['segments']:
			self.heat_map.append_segment(self._get_segment_time(segment))
		# print(self.heat_map.ranges)
		
		consensus_time = 0
		reached_consensus = False
		range_overlaps = self.heat_map.get_overlapping_ranges(self.living_audio.duration_seconds)
		# print(range_overlaps)
		
		if len(range_overlaps) > 1:
			sufficent_overlap = False
			for overlap in range_overlaps:
				if overlap.count >= self.concensus_transcription_threshold:
					sufficent_overlap = True
			
			if sufficent_overlap:
				l = range_overlaps[-1].length()
				if l > self.consensus_threshold:
					consensus_time = min(l, self.consensus_threshold) / 2
					reached_consensus = True
					
		if reached_consensus:
			self.previous_consensus_time = consensus_time

			# Transcribe the accumulated living audio using the large model
			result_large = self.large_model.transcribe(self.living_audio)

			# Update fixed transcription
			self.fixed_transcription += result_large['text']
			
			self._clip(consensus_time, "consensus")
			self.heat_map.ranges.clear()

			return TranscriptionState(fixed_transcription=self.fixed_transcription, 
									  living_transcription="", 
									  length_added=len(result_large['text']))
		else:
			if self._run_count_since_clipped > self.concensus_transcription_threshold:
				transcriptions_detected = False
				for overlap in range_overlaps:
					if overlap.count > 0:
						transcriptions_detected = True
						break
				
				if not transcriptions_detected and self.living_audio.duration_seconds > self.consensus_threshold:
					self._run_count_since_clipped = 0
					self._clip(self.consensus_threshold/2, "no_transcriptions")
					self.heat_map.ranges.clear()
				
			return TranscriptionState(fixed_transcription=self.fixed_transcription, 
									  living_transcription=result_tiny['text'], 
									  length_added=0)
	
	def finish_transcription(self, audio_segment: AudioSegment = None) -> TranscriptionState:
		if audio_segment is not None:
			self.living_audio += audio_segment

		result_large = self.large_model.transcribe(self.living_audio)
		self.fixed_transcription += result_large['text']
		
		state = TranscriptionState(fixed_transcription=self.fixed_transcription, 
								  living_transcription="", 
								  length_added=len(result_large['text']))
		self.new_transcription()
		return state

	def _get_consensus_time(self, segments) -> float:
		_, last_segment_end = self._get_segment_time(segments[-2])
		next_segment_start, _ = self._get_segment_time(segments[-1])
		consensus_time = (last_segment_end + next_segment_start) / 2
		return min(consensus_time, self.consensus_threshold)

	def _get_segment_time(self, segment) -> (float, float):
		# Adjust the start and end times by the start time
		start = segment['start'] + self.start_time
		end = segment['end'] + self.start_time
		return start, end