from dataclasses import dataclass
from enum import Enum
from typing import List, Tuple


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