from ClassyFlaskDB.DefaultModel import *
from pydub import AudioSegment
from datetime import datetime

@DATA
@dataclass
class Audio(Object):
	segment: AudioSegment
	start_time: datetime
	
	@property
	def data_length(self) -> float:
		'''How much audio data we actually have in seconds'''
		return self.segment.duration_seconds
	
	@property
	def length(self) -> float:
		'''
		How much time between start and finish, including any
		dead air time we didn't actually record for some reason.
		(like skipped frames)
		'''
		return (self.date_created - self.start_time).total_seconds()