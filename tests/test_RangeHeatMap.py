import unittest
from AbstractAI.Helpers.RangeHeatMap import RangeHeatMap

class TestRangeHeatMap(unittest.TestCase):
	def test_get_overlapping_ranges_1(self):
		heat_map = RangeHeatMap()
		heat_map.append_segment((1, 2))
		heat_map.append_segment((3, 4))
		
		range_overlaps = heat_map.get_overlapping_ranges(5)
		# start:0, end:1, count:0
		# start:1, end:2, count:1
		# start:2, end:3, count:0
		# start:3, end:4, count:1
		# start:4, end:5, count:0
		self.assertEqual(len(range_overlaps), 5)
		self.assertEqual(range_overlaps[0].count, 0)
		self.assertEqual(range_overlaps[1].count, 1)
		self.assertEqual(range_overlaps[2].count, 0)
		self.assertEqual(range_overlaps[3].count, 1)
		self.assertEqual(range_overlaps[4].count, 0)
		
		self.assertEqual(range_overlaps[0].start, 0)
		self.assertEqual(range_overlaps[1].start, 1)
		self.assertEqual(range_overlaps[2].start, 2)
		self.assertEqual(range_overlaps[3].start, 3)
		self.assertEqual(range_overlaps[4].start, 4)
		
		self.assertEqual(range_overlaps[0].end, 1)
		self.assertEqual(range_overlaps[1].end, 2)
		self.assertEqual(range_overlaps[2].end, 3)
		self.assertEqual(range_overlaps[3].end, 4)
		self.assertEqual(range_overlaps[4].end, 5)
	
	def test_get_overlapping_ranges_2(self):
		heat_map = RangeHeatMap()
		heat_map.append_segment((1, 1.5))
		heat_map.append_segment((1.5, 2))
		
		range_overlaps = heat_map.get_overlapping_ranges(5)
		# start:0, end:1, count:0
		# start:1, end:2, count:1
		# start:2, end:5, count:0
		
		self.assertEqual(len(range_overlaps), 3)
		self.assertEqual(range_overlaps[0].count, 0)
		self.assertEqual(range_overlaps[1].count, 1)
		self.assertEqual(range_overlaps[2].count, 0)
		
		self.assertEqual(range_overlaps[0].start, 0)
		self.assertEqual(range_overlaps[1].start, 1)
		self.assertEqual(range_overlaps[2].start, 2)
		
		self.assertEqual(range_overlaps[0].end, 1)
		self.assertEqual(range_overlaps[1].end, 2)
		self.assertEqual(range_overlaps[2].end, 5)
	
	def test_get_overlapping_ranges_3(self):
		heat_map = RangeHeatMap()
		heat_map.append_segment((0, 1))
		heat_map.append_segment((1, 2))
		
		range_overlaps = heat_map.get_overlapping_ranges(5)
		# start:0, end:0, count:0
		# start:0, end:2, count:1
		# start:2, end:5, count:0
		
		self.assertEqual(len(range_overlaps), 3)
		self.assertEqual(range_overlaps[0].count, 0)
		self.assertEqual(range_overlaps[1].count, 1)
		self.assertEqual(range_overlaps[2].count, 0)
		
		self.assertEqual(range_overlaps[0].start, 0)
		self.assertEqual(range_overlaps[1].start, 0)
		self.assertEqual(range_overlaps[2].start, 2)
		
		self.assertEqual(range_overlaps[0].end, 0)
		self.assertEqual(range_overlaps[1].end, 2)
		self.assertEqual(range_overlaps[2].end, 5)
		
	def test_get_overlapping_ranges_4(self):
		heat_map = RangeHeatMap()
		heat_map.append_segment((0, 6.356733333333333))
		heat_map.append_segment((7.0, 8.0))
		heat_map.append_segment((6.0, 7.0))
		
		range_overlaps = heat_map.get_overlapping_ranges(10)
		# start:0, end:0, count:0
		# start:0, end:6, count:1
		# start:6, end:6.356733333333333, count:2
		# start:6.356733333333333, end:8, count:1
		# start:8, end:10, count:0
		
		self.assertEqual(len(range_overlaps), 5)
		self.assertEqual(range_overlaps[0].count, 0)
		self.assertEqual(range_overlaps[1].count, 1)
		self.assertEqual(range_overlaps[2].count, 2)
		self.assertEqual(range_overlaps[3].count, 1)
		self.assertEqual(range_overlaps[4].count, 0)
		
		self.assertEqual(range_overlaps[0].start, 0)
		self.assertEqual(range_overlaps[1].start, 0)
		self.assertEqual(range_overlaps[2].start, 6)
		self.assertEqual(range_overlaps[3].start, 6.356733333333333)
		self.assertEqual(range_overlaps[4].start, 8)
		
		self.assertEqual(range_overlaps[0].end, 0)
		self.assertEqual(range_overlaps[1].end, 6)
		self.assertEqual(range_overlaps[2].end, 6.356733333333333)
		self.assertEqual(range_overlaps[3].end, 8)
		self.assertEqual(range_overlaps[4].end, 10)
		
	def test_get_overlapping_ranges_5(self):
		heat_map = RangeHeatMap()
		heat_map.append_segment((.1, 1.5))
		heat_map.append_segment((1, 2))
		heat_map.append_segment((3, 4))
		heat_map.append_segment((3.5, 6))
		heat_map.append_segment((7, 8))
		heat_map.append_segment((.5, .8))
		
		range_overlaps = heat_map.get_overlapping_ranges(10)
		# start:0, end:0.1, count:0
		# start:0.1, end:0.5, count:1
		# start:0.5, end:0.8, count:2
		# start:0.8, end:1, count:1
		# start:1, end:1.5, count:2
		# start:1.5, end:2, count:1
		# start:2, end:3, count:0
		# start:3, end:3.5, count:1
		# start:3.5, end:4, count:2
		# start:4, end:6, count:1
		# start:6, end:7, count:0
		# start:7, end:8, count:1
		# start:8, end:10, count:0
		
		self.assertEqual(len(range_overlaps), 13)
		self.assertEqual(range_overlaps[0].count, 0)
		self.assertEqual(range_overlaps[1].count, 1)
		self.assertEqual(range_overlaps[2].count, 2)
		self.assertEqual(range_overlaps[3].count, 1)
		self.assertEqual(range_overlaps[4].count, 2)
		self.assertEqual(range_overlaps[5].count, 1)
		self.assertEqual(range_overlaps[6].count, 0)
		self.assertEqual(range_overlaps[7].count, 1)
		self.assertEqual(range_overlaps[8].count, 2)
		self.assertEqual(range_overlaps[9].count, 1)
		self.assertEqual(range_overlaps[10].count, 0)
		self.assertEqual(range_overlaps[11].count, 1)
		self.assertEqual(range_overlaps[12].count, 0)
		
		self.assertEqual(range_overlaps[0].start, 0)
		self.assertEqual(range_overlaps[1].start, .1)
		self.assertEqual(range_overlaps[2].start, .5)
		self.assertEqual(range_overlaps[3].start, .8)
		self.assertEqual(range_overlaps[4].start, 1)
		self.assertEqual(range_overlaps[5].start, 1.5)
		self.assertEqual(range_overlaps[6].start, 2)
		self.assertEqual(range_overlaps[7].start, 3)
		self.assertEqual(range_overlaps[8].start, 3.5)
		self.assertEqual(range_overlaps[9].start, 4)
		self.assertEqual(range_overlaps[10].start, 6)
		self.assertEqual(range_overlaps[11].start, 7)
		self.assertEqual(range_overlaps[12].start, 8)
		
		self.assertEqual(range_overlaps[0].end, .1)
		self.assertEqual(range_overlaps[1].end, .5)
		self.assertEqual(range_overlaps[2].end, .8)
		self.assertEqual(range_overlaps[3].end, 1)
		self.assertEqual(range_overlaps[4].end, 1.5)
		self.assertEqual(range_overlaps[5].end, 2)
		self.assertEqual(range_overlaps[6].end, 3)
		self.assertEqual(range_overlaps[7].end, 3.5)
		self.assertEqual(range_overlaps[8].end, 4)
		self.assertEqual(range_overlaps[9].end, 6)
		self.assertEqual(range_overlaps[10].end, 7)
		self.assertEqual(range_overlaps[11].end, 8)
		self.assertEqual(range_overlaps[12].end, 10)
		
	def test_get_overlapping_ranges_6(self):
		heat_map = RangeHeatMap()
		heat_map.append_segment((0, 1))
		heat_map.append_segment((1, 2))
		heat_map.append_segment((2, 3))
		heat_map.append_segment((3, 4))
		
		range_overlaps = heat_map.get_overlapping_ranges(5)
		# start:0, end:0, count:0
		# start:0, end:4, count:1
		# start:4, end:5, count:0
		
		self.assertEqual(len(range_overlaps), 3)
		self.assertEqual(range_overlaps[0].count, 0)
		self.assertEqual(range_overlaps[1].count, 1)
		self.assertEqual(range_overlaps[2].count, 0)
		
		self.assertEqual(range_overlaps[0].start, 0)
		self.assertEqual(range_overlaps[1].start, 0)
		self.assertEqual(range_overlaps[2].start, 4)
		
		self.assertEqual(range_overlaps[0].end, 0)
		self.assertEqual(range_overlaps[1].end, 4)
		self.assertEqual(range_overlaps[2].end, 5)
		
	def test_get_overlapping_ranges_7(self):
		heat_map = RangeHeatMap()
		heat_map.append_segment((1, 2))
		heat_map.append_segment((1.5, 3))
		heat_map.append_segment((1.6, 3.5))
		heat_map.append_segment((1.7, 4))
		heat_map.append_segment((1.8, 4.5))
		
		range_overlaps = heat_map.get_overlapping_ranges(5)
		# start:0, end:1, count:0
		# start:1, end:1.5, count:1
		# start:1.5, end:1.6, count:2
		# start:1.6, end:1.7, count:3
		# start:1.7, end:1.8, count:4
		# start:1.8, end:2, count:5
		# start:2, end:3, count:4
		# start:3, end:3.5, count:3
		# start:3.5, end:4, count:2
		# start:4, end:4.5, count:1
		# start:4.5, end:5, count:0
		
		self.assertEqual(len(range_overlaps), 11)
		self.assertEqual(range_overlaps[0].count, 0)
		self.assertEqual(range_overlaps[1].count, 1)
		self.assertEqual(range_overlaps[2].count, 2)
		self.assertEqual(range_overlaps[3].count, 3)
		self.assertEqual(range_overlaps[4].count, 4)
		self.assertEqual(range_overlaps[5].count, 5)
		self.assertEqual(range_overlaps[6].count, 4)
		self.assertEqual(range_overlaps[7].count, 3)
		self.assertEqual(range_overlaps[8].count, 2)
		self.assertEqual(range_overlaps[9].count, 1)
		self.assertEqual(range_overlaps[10].count, 0)
		
		self.assertEqual(range_overlaps[0].start, 0)
		self.assertEqual(range_overlaps[1].start, 1)
		self.assertEqual(range_overlaps[2].start, 1.5)
		self.assertEqual(range_overlaps[3].start, 1.6)
		self.assertEqual(range_overlaps[4].start, 1.7)
		self.assertEqual(range_overlaps[5].start, 1.8)
		self.assertEqual(range_overlaps[6].start, 2)
		self.assertEqual(range_overlaps[7].start, 3)
		self.assertEqual(range_overlaps[8].start, 3.5)
		self.assertEqual(range_overlaps[9].start, 4)
		self.assertEqual(range_overlaps[10].start, 4.5)
		
		self.assertEqual(range_overlaps[0].end, 1)
		self.assertEqual(range_overlaps[1].end, 1.5)
		self.assertEqual(range_overlaps[2].end, 1.6)
		self.assertEqual(range_overlaps[3].end, 1.7)
		self.assertEqual(range_overlaps[4].end, 1.8)
		self.assertEqual(range_overlaps[5].end, 2)
		self.assertEqual(range_overlaps[6].end, 3)
		self.assertEqual(range_overlaps[7].end, 3.5)
		self.assertEqual(range_overlaps[8].end, 4)
		self.assertEqual(range_overlaps[9].end, 4.5)
		self.assertEqual(range_overlaps[10].end, 5)		
		
if __name__ == '__main__':
	unittest.main()