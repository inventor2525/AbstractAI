from ClassyFlaskDB.DATA import *
from datetime import datetime
from typing import List, Dict

from pydub import AudioSegment
import math
STTLog = DATADecorator()

@STTLog
class AudioFile:
	path : str = None
	length : float = 0
	_audio_segment : AudioSegment = field(init=False, default=None, hash=False, repr=False, compare=False)

@STTLog(generated_id_type=ID_Type.HASHID)
class ModelInfo:
	name : str = None
	remote : bool = False

@STTLog
class Clip:
	key: str = field(default=None, kw_only=True)
	file : AudioFile = field(default_factory=AudioFile, kw_only=True)
	end : datetime = field(default=None, kw_only=True)
	transcribed : bool = field(default=False, kw_only=True)
	
@STTLog
class Recording(Clip):
	start : datetime = field(default_factory=datetime.now, kw_only=True)
	
	children : List["Clip"] = field(default_factory=list, kw_only=True)

@STTLog
class Transcription:
	audio : Clip
	model : ModelInfo
	
	start: datetime = field(default_factory=datetime.now)
	end: datetime = None
	
	text : str = None
	raw : Dict[str, str] = None
	max_no_speech_prob : float = -math.inf

stt_logger_engine = DATAEngine(STTLog, engine_str='sqlite:///stt_log.db')