from AbstractAI.TextToSpeech.TTS import *
from AbstractAI.Model.Settings.Kokoro_TTS_Settings import Kokoro_TTS_Settings
from kokoro import KPipeline
import soundfile as sf
import numpy as np

@dataclass
class Kokoro_TTS(TTS):
	settings:Kokoro_TTS_Settings
	pipeline:KPipeline = field(default=None, init=False)
	
	def __post_init__(self):
		super().__post_init__()
		self.pipeline = KPipeline(lang_code=self.settings.lang_code)
	
	def _setup_job(self, job:TTSJob):
		job.data.model = self.settings
		
	def work(self, job:TTSJob) -> JobStatus:
		if job.data.text and len(job.data.text)>0:
			with safe_stopwatch.scope():
				safe_stopwatch("Request")
				
				audios = []
				generator = self.pipeline(
					job.data.text, voice=self.settings.voice,
					speed=self.settings.speed,
					split_pattern=self.settings.split_pattern
				)
				for i, (gs, ps, audio) in enumerate(generator):
					# print(i)  # i => index
					# print(gs) # gs => graphemes/text
					# print(ps) # ps => phonemes
					# sf.write(f'{i}.wav', audio, 24000)
					audios.append( np.array(audio) )
				
				safe_stopwatch("Save")
				combined_audio = np.concatenate(audios, axis=0)
				sf.write('temp.wav', combined_audio, 24000)
				
				safe_stopwatch("Create AudioSegment")
				audio_segment = AudioSegment.from_mp3("temp.wav")
				#TODO: do this in memory, not by a double save ^^
				job.data.speech = audio_segment
		return JobStatus.SUCCESS