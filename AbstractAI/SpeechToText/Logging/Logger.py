from AbstractAI.SpeechToText.Logging.Model import *
import os
from datetime import datetime
from werkzeug.datastructures import FileStorage
from flask import request
import mimetypes

from pydub import AudioSegment

class Logger:
	def __init__(self, files_folder="speech_to_text_files"):
		self.files_folder = files_folder
		self.segments:Dict[str, Recording] = {}
		
	def start_segment(self, key:str, child_of:str=None) -> Recording:
		self.segments[key] = Recording(key=key)
		if child_of is not None:
			self.segments[child_of].children.append(self.segments[key])
		return self.segments[key]
		
	def end_segment(self, key:str, audio_segment:AudioSegment) -> Recording:
		self._save_audio_to_clip(audio_segment, self.segments[key])
		
		stt_logger_engine.merge(self.segments[key])
		return self.segments[key]
	
	def log_clip(self, audio_segment:AudioSegment, key:str, child_of:str=None) -> Clip:
		clip = Clip(key=key)
		self._save_audio_to_clip(audio_segment, clip)
		stt_logger_engine.merge(clip)
		if child_of is not None:
			self.segments[child_of].children.append(clip)
		return clip
	
	def _save_audio_to_clip(self, audio_segment:AudioSegment, clip:Clip):
		clip.end = datetime.now()
		
		path = os.path.join(self.files_folder, clip.key, f"{clip.end.strftime('%Y-%m-%d_%H-%M-%S.%f')}.wav")
		os.makedirs(os.path.dirname(path), exist_ok=True)
		
		audio_segment.export(path, format="wav")
		clip.file.path = path
		clip.file.length = audio_segment.duration_seconds
		
stt_logger = Logger()