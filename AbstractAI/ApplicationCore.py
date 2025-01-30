# Setup StopWatch (for application timing):
from AbstractAI.Helpers.Stopwatch import Stopwatch
Stopwatch.singleton = Stopwatch(should_log=True, log_statistics=False)
stopwatch = Stopwatch.singleton

# Track import times:
stopwatch("AbstractAI App Core Init")
stopwatch.new_scope()

stopwatch("Basics")
import json
from enum import Enum
from pydub import AudioSegment
from datetime import datetime
from copy import deepcopy
import argparse
import shutil
import os

stopwatch("nltk")
import nltk
from nltk.tokenize import word_tokenize
nltk.download('punkt')

stopwatch("ClassyFlaskDB")
from ClassyFlaskDB.DefaultModel import *
from ClassyFlaskDB.new.AudioTranscoder import AudioTranscoder
from ClassyFlaskDB.new.SQLStorageEngine import SQLStorageEngine
from ClassyFlaskDB.new.JSONStorageEngine import JSONStorageEngine

stopwatch("Helpers")
from AbstractAI.Helpers.ScopeParams import *
from AbstractAI.Helpers.Signal import Signal, LazySignal
from AbstractAI.Helpers.Jobs import *

stopwatch("LLMSettings")
from AbstractAI.Model.Settings.LLMSettings import *
llm_settings_types = LLMSettings.load_subclasses()

stopwatch("Conversation Model")
from AbstractAI.Model.Converse import *

stopwatch("TTS Settings")
from AbstractAI.Model.Settings.STT_Settings import *

stopwatch("Artifacts")
from AbstractAI.Model.Artifacts import TextArtifact, TextArtifacts, TextFileArtifact

stopwatch("Conversable")
from AbstractAI.Conversable import *
from AbstractAI.LLMs.LLM import LLM
from AbstractAI.Automation.Agent import Agent, AgentConfig
from AbstractAI.LLMs.LLM_Helpers import ResponseObject, LLMParams, LLMJob

stopwatch("Audio IO")
from AbstractAI.Helpers.AudioPlayer import AudioPlayer
from AbstractAI.Helpers.AudioRecorder import AudioRecorder

stopwatch.start("Speech to Text")
from AbstractAI.SpeechToText.Transcriber import Transcriber, Transcription, TranscriptionJob
from AbstractAI.SpeechToText.VAD import VAD, VADSettings
from AbstractAI.SpeechToText.TranscriptionIterator import TranscriptionIterator
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
	
	db_version: str = "v3"
	# Current db version
	
	prev_compatible_db_versions: List[str] = default([])
	# Previous versions of the db that are compatible to load with this one.
	
	#######################
	#       State         #
	#######################
	_settings: List[Tuple[Object, Optional[Callable[[],None]]]] = field(default_factory=list, init=False)
	# All settings we will save when calling 'save settings'
	
	_llm_cache:Dict[str, LLMSettings] = field(default_factory=dict, init=False)
	# Mapping for all LLMs based on 'user model name'
	
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
		self.stt_settings = self.query_db(STT_Settings_v1, as_setting=True)
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
		self.transcriber = Transcriber(self.stt_settings)

		# Create Voice Activity Detector:
		#TODO: VAD (with offline mode):
		stopwatch("Voice Activity Detector startup")
		self.vad = VAD(self.vad_settings, self.audio_recorder)
		
		# Setup Text to Speech:
		stopwatch("Text to Speech startup")
		self.tts = OpenAI_TTS(self.speech_settings, callback=self.text_to_speech_callback)
		
		# Load any previously un-completed jobs:
		stopwatch("Query Jobs")
		AppContext.jobs = self.query_db(Jobs)
		AppContext.jobs.changed.connect(self.save_jobs)
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
	
	def save_settings(self, engine:Optional[StorageEngine]=None) -> None:
		'''
		Save all 'settings' registered with 'register_setting' to the
		passed storage engine, or to the one in app context if none
		is passed.
		'''
		if engine is None:
			engine = AppContext.engine
		
		for model in self.llmConfigs.models:
			model.new_id(True)
		
		for setting, on_save in self._settings:
			if on_save:
				on_save()
			engine.merge(setting)
	
	def export_settings(self, path:Optional[str]=None) -> dict:
		engine = JSONStorageEngine(DATA)
		self.save_settings(engine)
		settings = engine._data
		if path:
			directory = os.path.dirname(path)
			if len(directory)>0 and not os.path.exists(directory):
				os.makedirs(directory, exist_ok=True)
			with open(path, "w") as f:
				json.dump(settings, f, indent=4)
		return settings
	
	def import_settings(self, settings:Union[str, dict]) -> None:
		'''
		Imports the settings provided or at the path provided,
		into the main storage engine.
		'''
		if isinstance(settings, str):
			with open(settings, "r") as f:
				settings = json.load(f)
		
		def copy_into(new_obj, old_obj, closed_set:set=set()):
			ci = ClassInfo.get(type(new_obj))
			for field in ci.fields.values():
				if field.name == ci.primary_key_name:
					continue
				
				new_val = getattr(new_obj, field.name)
				if ClassInfo.get(field.type) is None:
					setattr(old_obj, field.name, new_val)
				else:
					old_val = getattr(old_obj, field.name)
					if old_val is None:
						setattr(old_obj, field.name, new_val)
					elif old_val not in closed_set:
						closed_set.add(old_val)
						copy_into(new_val, old_val, closed_set=closed_set)
		
		json_llm_settings :LLMConfigs = None
		engine = JSONStorageEngine(DATA, initial_data=settings)
		for setting_t in self._settings:
			setting = setting_t[0]
			setting_type = type(setting)
			
			json_setting = engine.query(setting_type).first()
			if setting_type is LLMConfigs:
				json_llm_settings = json_setting
				continue
			
			if json_setting is not None:
				copy_into(json_setting, setting)
			
		if json_llm_settings:
			exiting_models = {(type(model), model.user_model_name):model for model in self.llmConfigs.models}
			for model in json_llm_settings.models:
				model_key = (type(model), model.user_model_name)
				if model_key in exiting_models:
					old_model = exiting_models[model_key]
					copy_into(model, old_model)
				else:
					self.llmConfigs.models.append(model)
		
		self.save_settings()
		
	def _save_job(self, job:Job) -> None:
		'''Save's a single job. (triggered by Jobs.should_save_job after job completes)'''
		with AppContext.jobs._lock:
			AppContext.engine.merge(job)
	
	def save_jobs(self) -> None:
		'''Saves current jobs list to the db. (triggered by Jobs.changed event)'''
		with AppContext.jobs._lock:
			AppContext.engine.merge(AppContext.jobs)
	
	def transcription_work(self, job: TranscriptionJob) -> JobStatus:
		if job.audio:
			job.transcription = self.transcriber.transcribe(job.audio)
			return JobStatus.SUCCESS
		job.status_hover = "No audio supplied for transcription."
		return JobStatus.FAILED

	def transcription_callback(self, job: TranscriptionJob):
		self.transcription_completed(job.transcription)
	
	def text_to_speech_callback(self, job:TTSJob):
		#self.audio_player.play(job.data.speech)
		from pydub.playback import play
		play(job.data.speech)
		self.done_speaking = True
		
	def transcribe_live(self) -> Iterator[Transcription]:
		with TranscriptionIterator(self.audio_recorder, self.vad, stream_path="/home/charlie/_temp_stream_audio") as iterator:
			yield from iterator
			
	def __getitem__(self, model_name: str) -> LLM:
		if model_name not in self._llm_cache:
			for model_settings in self.llmConfigs.models:
				if model_settings.user_model_name == model_name:
					self._llm_cache[model_name] = model_settings
					break
			else:
				raise KeyError(f"No LLM model found with name: {model_name}")
		return self._llm_cache[model_name].model
	
	def llm_method(self, llm:LLM, key:str=None, with_history:bool=False, blocking:bool=True):
		from AbstractAI.LLMs.LLM_Helpers import llm_method
		return llm_method(
			llm=llm, key=key, 
			with_history=with_history, 
			blocking=blocking
		)
	
	def speak(self, text:str, blocking:bool=True):
		self.done_speaking = False
		self.tts.speak(text)
		if blocking:
			while not getattr(self, 'done_speaking', False):
				time.sleep(0.01)
	
	def quit(self):
		'''Do all things needed to do before terminating the application.'''
		if getattr(self, 'has_quit', False):
			self.has_quit = True
			return
		
		AppContext.jobs.stop()
		self.save_jobs()
		self.save_settings()
	
	def sanitize_text(self, text:str) -> str:
		'''
		Makes text all lower case and removes all punctuation.
		'''
		# Tokenize the text
		tokens = word_tokenize(text.lower())
		
		# Remove punctuation and numbers
		tokens = [token for token in tokens if token.isalpha()]
		
		# Join the tokens back into a string
		processed_text = ' '.join(tokens)
		return processed_text.strip()
		
stopwatch.end_scope() #AbstractAI App Core Init
stopwatch("")