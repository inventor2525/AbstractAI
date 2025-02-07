from AbstractAI.AppContext import AppContext
from AbstractAI.Model.Converse import DATA
from AbstractAI.Helpers.Jobs import Job, Jobs, JobStatus
from AbstractAI.Helpers.Stopwatch import SafeStopwatch
from ClassyFlaskDB.DefaultModel import Object
from dataclasses import dataclass, field
from pydub import AudioSegment
from typing import Callable

safe_stopwatch = SafeStopwatch.singleton

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
	callback:Callable[[TTSJob], None] = field(default=None, kw_only=True)
	
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
		AppContext.jobs.add(job)
		return job
	
	def work(self, job:TTSJob) -> JobStatus:
		pass
	
	def on_callback(self, job:TTSJob):
		if self.callback:
			self.callback(job)