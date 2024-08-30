from ClassyFlaskDB.DefaultModel import *

@DATA
@dataclass
class OpenAI_TTS_Settings(Object):
    __ui_name__ = "OpenAI TTS"
    api_key: str = ""
    model: str = "tts-1"
    voice: str = "alloy"