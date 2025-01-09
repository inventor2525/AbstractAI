from ClassyFlaskDB.DefaultModel import *
from datetime import datetime

@DATA
@dataclass
class Vector2:
	x: int
	y: int

@DATA
@dataclass
class ScreenDump:
	raw_text: str
	color_json: dict
	cursor_position: Vector2
	timestamp: datetime = field(default_factory=get_local_time)

@DATA
@dataclass
class Output:
	raw_bytes: bytes
	timestamp: datetime = field(default_factory=get_local_time)
	_string: str = field(default=None, init=False, repr=False)
	
	@property
	def string(self) -> str:
		if self._string is None:
			self._string = self.raw_bytes.decode('utf-8', errors='ignore')
		return self._string