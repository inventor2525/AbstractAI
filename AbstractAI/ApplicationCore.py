# Setup StopWatch (for application timing):
from AbstractAI.Helpers.Stopwatch import Stopwatch
Stopwatch.singleton = Stopwatch(should_log=True, log_statistics=False)
stopwatch = Stopwatch.singleton

# Track import times:
stopwatch("AbstractAI App Core Startup")
stopwatch.new_scope()
stopwatch("Imports")
stopwatch.new_scope()

stopwatch("Basics")
import json
from pydub import AudioSegment
from datetime import datetime
from copy import deepcopy
import argparse
import shutil
import os

stopwatch("ClassyFlaskDB")
from ClassyFlaskDB.DefaultModel import *
from ClassyFlaskDB.new.AudioTranscoder import AudioTranscoder
from ClassyFlaskDB.new.SQLStorageEngine import SQLStorageEngine

stopwatch("Helpers")
from AbstractAI.Helpers.Signal import Signal
from AbstractAI.Helpers.Jobs import *

stopwatch("LLMSettings")
from AbstractAI.Model.Settings.LLMSettings import *
llm_settings_types = LLMSettings.load_subclasses()

stopwatch("Conversation Model")
from AbstractAI.Model.Converse import *

stopwatch("TTS Settings")
from AbstractAI.Model.Settings.TTS_Settings import *

stopwatch("Conversable")
from AbstractAI.Conversable import *
from AbstractAI.LLMs.LLM import LLM
from AbstractAI.Automation.Agent import Agent, AgentConfig

stopwatch("Audio IO")
from AbstractAI.Helpers.AudioPlayer import AudioPlayer
from AbstractAI.Helpers.AudioRecorder import AudioRecorder

stopwatch.start("Speech to Text")
from AbstractAI.SpeechToText.Transcriber import Transcriber, Transcription, TranscriptionJob
from AbstractAI.SpeechToText.VAD import VAD, VADSettings
stopwatch.stop("Speech to Text")

stopwatch("Text to Speech")
from AbstractAI.Model.Settings.OpenAI_TTS_Settings import OpenAI_TTS_Settings
from AbstractAI.TextToSpeech.TTS import OpenAI_TTS, TTSJob

stopwatch("Context")
from AbstractAI.AppContext import AppContext

stopwatch("Application")
T = TypeVar("T")

@dataclass
class ApplicationCore:
	#######################
	#      Config         #
	#######################
	storage_location: str
	# The un-versioned root directory all application data will be stored in
	
	db_version: str = "v2.1"
	# Current db version
	
	prev_compatible_db_versions: List[str] = default(["v2.0"])
	# Previous versions of the db that are compatible to load with this one.
	
	#######################
	#       State         #
	#######################
	_settings: List[Tuple[Object, Optional[Callable[[],None]]]] = field(default_factory=list, init=False)
	# All settings we will save when calling 'save settings'
	
	#######################
	#      Signals        #
	#######################
	transcription_completed: Signal[[Transcription],None] = Signal[[Transcription],None].field()
	
	def __post_init__(self) -> None:
		stopwatch("AIApplication.init")
		stopwatch.new_scope()
		
		# Get storage locations:
		stopwatch("Path generation")
		if self.storage_location.endswith(".db"):
			self.storage_location = self.storage_location[:-3]
		AppContext.storage_location = self.storage_location
		
		files_path = os.path.join(AppContext.storage_location, "files")
		os.makedirs(files_path, exist_ok=True)
		
		db_path = os.path.join(AppContext.storage_location, self.db_version, "chat.db")
		os.makedirs(os.path.join(AppContext.storage_location, self.db_version), exist_ok=True)
		
		# Migrate old db if needed (and possible):
		if not os.path.exists(db_path):
			stopwatch("DB version migrate")
			for version in self.prev_compatible_db_versions:
				old_db_path = os.path.join(AppContext.storage_location, version, "chat.db")
				if os.path.exists(old_db_path):
					shutil.copyfile(old_db_path, db_path)
		
		# Load/Create & link the database to model classes:
		stopwatch("DB startup")
		AppContext.engine = SQLStorageEngine(f"sqlite:///{db_path}", DATA, files_dir=files_path)
		
		# Load all settings:
		stopwatch("Query Settings")
		self.llmConfigs = self.query_db(LLMConfigs, as_setting=True)
		self.vad_settings = self.query_db(VADSettings, as_setting=True)
		self.transcription_settings = self.query_db(Hacky_Whisper_Settings, as_setting=True)
		self.speech_settings = self.query_db(OpenAI_TTS_Settings, as_setting=True)
		
		# Create User Source:
		AppContext.user_source = UserSource() | CallerInfo.catch([0])
		
		# Load conversations:
		stopwatch("Load Conversations")
		self.conversations = ConversationCollection.all_from_engine(AppContext.engine)
		
		# Start up audio IO:
		self.audio_recorder = AudioRecorder()
		self.audio_player = AudioPlayer()
		
		# Create Transcriber:
		stopwatch("Transcriber startup")
		self.transcriber = Transcriber(self.transcription_settings, recorder=self.audio_recorder, player=self.audio_player)
		AppContext.transcriber = self.transcriber #Legacy bs (moving it to self cause circular import)
		
		# Create Voice Activity Detector:
		#TODO: VAD (with offline mode):
		stopwatch("Voice Activity Detector startup")
		self.vad = VAD(self.vad_settings, self.audio_recorder)
		
		# Setup Text to Speech:
		stopwatch("Text to Speech startup")
		self.stt = OpenAI_TTS(self.speech_settings)
		
		# Load any previously un-completed jobs:
		stopwatch("Query Jobs")
		AppContext.jobs = self.query_db(Jobs)
		AppContext.jobs.changed.connect(self._save_jobs)
		AppContext.jobs.should_save_job.connect(self._save_job)
		
		# Job registration:
		Jobs.register("Transcribe", self.transcription_work, self.transcription_callback)
		
		# Start processing jobs:
		stopwatch("Start Jobs")
		AppContext.jobs.start()
		
		stopwatch.end_scope() #AIApplication.init
	
	def register_setting(self, setting_obj:T, on_save:Optional[Callable[[],None]]=None) -> T:
		'''
		Helper method to maintain a list of 'settings' objects
		that will be saved when save_settings is called.
		
		Pass on_save for anything you wish to do prior to a save event.
		
		Returns setting_obj for convenience.
		'''
		self._settings.append((setting_obj, on_save))
		return setting_obj
	
	def query_db(self, obj_type:Type[T], as_setting=False) -> T:
		'''
		Query the db for an object of type,
		construct it if it does not exist, and 
		registering it as a 'setting' to be saved as
		one when 'settings' are saved if as_setting is True.
		'''
		obj = AppContext.engine.query(obj_type).first()
		if obj is None:
			obj = obj_type()
		if as_setting:
			return self.register_setting(obj)
		return obj
	
	def save_settings(self) -> None:
		'''Save all 'settings' registered with 'register_setting' to the db.'''
		for model in self.llmConfigs.models:
				model.new_id(True)
		
		for setting, on_save in self._settings:
			if on_save:
				on_save()
			AppContext.engine.merge(setting)
	
	def _save_job(self, job:Job) -> None:
		'''Save's a single job. (triggered by Jobs.should_save_job after job completes)'''
		with AppContext.jobs._lock:
			AppContext.engine.merge(job)
	
	def _save_jobs(self) -> None:
		'''Saves current jobs list to the db. (triggered by Jobs.changed event)'''
		with AppContext.jobs._lock:
			AppContext.engine.merge(AppContext.jobs)
	
	def transcription_work(self, job: TranscriptionJob) -> JobStatus:
		if job.transcription:
			self.transcriber.transcribe(job.transcription)
			return JobStatus.SUCCESS
		job.status_hover = "No transcription object supplied."
		return JobStatus.FAILED

	def transcription_callback(self, job: TranscriptionJob):
		self.transcription_completed(job.transcription)
		
stopwatch.end_scope() #Imports


stopwatch.end_scope() # AbstractAI App Core Startup

if __name__ == "__main__":
	appCore = ApplicationCore("/home/charlie/Documents/AbstractAI")
	print("Hello")