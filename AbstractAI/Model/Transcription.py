from AbstractAI.Model.Artifacts import TextArtifact
from AbstractAI.Model.Audio import *

@DATA
@dataclass
class Transcription(TextArtifact):
	audio: Audio
	transcription_time: float = field(default=None, init=False)
	raw_data: dict = field(default_factory=dict, init=False)
	
	@property
	def transcription_rate(self) -> float:
		'''How many seconds of audio was transcribed per second of compute?'''
		return self.audio.length / self.transcription_time