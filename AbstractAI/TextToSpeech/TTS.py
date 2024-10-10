from AbstractAI.UI.Context import Context
from AbstractAI.Model.Converse import DATA
from AbstractAI.Helpers.Jobs import Job, Jobs, JobStatus
from ClassyFlaskDB.DefaultModel import Object
from dataclasses import dataclass
from pydub import AudioSegment
from typing import Callable

@DATA
@dataclass
class TTSData(Object):
	text:str
	speech:AudioSegment = None
	model:Object = None

@DATA(excluded_fields=["callback", "work", "status_changed", "should_stop", "jobs"])
@dataclass
class TTSJob(Job):
	data:TTSData = None

@dataclass
class TTS:
	callback:Callable[[TTSJob], None]
	
	def __post_init__(self):
		Jobs.register("TTS", self.work, self.on_callback)
	
	def _setup_job(self, job:TTSJob):
		pass
	
	def speak(self, text:str) -> TTSJob:
		job = TTSJob(
			job_key="TTS", name="Text To Speech",
			data=TTSData(text)
		)
		self._setup_job(job)
		Context.engine.merge(job)
		Context.jobs.add(job)
		return job
	
	def work(self, job:TTSJob) -> JobStatus:
		pass
	
	def on_callback(self, job:TTSJob):
		self.callback(job)

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
			response = self.client.audio.speech.create(
				model=self.settings.model,
				voice=self.settings.voice,
				input=job.data.text
			)
			response.write_to_file("temp.mp3")
			audio_segment = AudioSegment.from_mp3("temp.mp3")
			#TODO: do this in memory, not by a double save ^^
			job.data.speech = audio_segment
		return JobStatus.SUCCESS