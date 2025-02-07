from ClassyFlaskDB.DefaultModel import *

@DATA
@dataclass
class Kokoro_TTS_Settings(Object):
    __ui_name__ = "Kokoro TTS"
    lang_code: str = "a"
    voice: str = "af_heart"
    speed: float = 1
    split_pattern: str = r'\n+'