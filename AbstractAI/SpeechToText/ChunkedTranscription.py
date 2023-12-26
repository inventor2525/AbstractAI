from AbstractAI.SpeechToText.WhisperSTT import WhisperSTT

from dataclasses import dataclass
from pydub import AudioSegment
import random

from dataclasses import dataclass
from enum import Enum
from typing import List, Tuple
import time

def is_near(a: float, b: float, epsilon: float = 0.001) -> bool:
	"""Check if two floating-point numbers are near each other within epsilon."""
	return abs(a - b) < epsilon

class RangeHeatMap:
	class PointType(Enum):
		START = 1
		END = -1
		
	@dataclass
	class Overlap:
		start: float
		end: float
		count: int
		
		def length(self):
			return self.end - self.start

	def __init__(self, ranges: List[Tuple[float, float]] = None):
		if ranges is None:
			ranges = []
		self.ranges = ranges

	def append_segment(self, range: Tuple[float, float]):
		self.ranges.append(range)

	def get_overlap_count(self, time_point: float) -> int:
		return sum(start <= time_point < end for start, end in self.ranges)
	
	def _include_end(self, end: float, last_end: float) -> bool:
		if end == 0:
			return False
		return end > last_end
	
	def get_overlapping_ranges(self, end: float = 0) -> List[Overlap]:
		if not self.ranges:
			return [self.Overlap(start=0, end=end, count=0)]
		
		if len(self.ranges) == 1:
			the_range = self.ranges[0]
			if self._include_end(end, the_range[1]):
				return [self.Overlap(start=0, end=the_range[0], count=0),
						self.Overlap(start=the_range[0], end=the_range[1], count=1),
						self.Overlap(start=the_range[1], end=end, count=0)]
			else:
				return [self.Overlap(start=0, end=0, count=0),
						self.Overlap(start=the_range[0], end=the_range[1], count=1)]
		
		
		points = [(start, self.PointType.START) for start, _ in self.ranges] + [(end, self.PointType.END) for _, end in self.ranges]
		
		# Sort points based on the time point only
		points.sort(key=lambda x: x[0])

		overlap_count = 0
		overlaps = []
		current_start = 0
		ran_once = False
		last_end = 0
		
		for point, type in points:
			if type == self.PointType.START:
				if ran_once:
					overlaps.append(self.Overlap(start=current_start, end=point, count=overlap_count))
				current_start = point
				overlap_count += 1
			else:  # PointType.END
				if not is_near(current_start, point):
					overlaps.append(self.Overlap(start=current_start, end=point, count=overlap_count))
					current_start = point
				overlap_count -= 1
			ran_once = True
			last_end = max(last_end, point)

		new_overlaps = [self.Overlap(start=0, end=points[0][0], count=0)]
		for i, current_overlap in enumerate(overlaps):
			if i > 0 and overlaps[i - 1].count == current_overlap.count and \
			(is_near(overlaps[i - 1].end, current_overlap.start) or overlaps[i - 1].end >= current_overlap.start):
				# Merge with previous overlap if counts are same and they are adjacent or overlapping
				new_overlaps[-1].end = max(new_overlaps[-1].end, current_overlap.end)
			else:
				# Add new overlap
				new_overlaps.append(current_overlap)
		
		if last_end < end:
			new_overlaps.append(self.Overlap(start=last_end, end=end, count=0))

		return new_overlaps

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
		
		# Initialize RangeHeatMap
		heat_map = RangeHeatMap()
		for segment in result_tiny['segments']:
			heat_map.append_segment(self._get_segment_time(segment))
		
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