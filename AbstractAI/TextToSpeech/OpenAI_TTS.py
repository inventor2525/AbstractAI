from AbstractAI.TextToSpeech.TTS import *
from openai import OpenAI
from AbstractAI.Model.Settings.OpenAI_TTS_Settings import OpenAI_TTS_Settings

@dataclass
class OpenAI_TTS(TTS):
	settings:OpenAI_TTS_Settings
	client:OpenAI = None
	
	def __post_init__(self):
		super().__post_init__()
		self.client = OpenAI(api_key=self.settings.api_key)
	
	def _setup_job(self, job:TTSJob):
		job.data.model = self.settings
		
	def work(self, job:TTSJob) -> JobStatus:
		if job.data.text and len(job.data.text)>0:
			with safe_stopwatch.scope():
				safe_stopwatch("Request")
				response = self.client.audio.speech.create(
					model=self.settings.model,
					voice=self.settings.voice,
					input=job.data.text
				)
				safe_stopwatch("Save")
				response.write_to_file("temp.mp3")
				safe_stopwatch("Create AudioSegment")
				audio_segment = AudioSegment.from_mp3("temp.mp3")
				#TODO: do this in memory, not by a double save ^^
				job.data.speech = audio_segment
		return JobStatus.SUCCESS